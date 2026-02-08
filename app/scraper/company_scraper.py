from bs4 import BeautifulSoup
from typing import Optional
import re
from .base import BaseScraper
from .parsers import TableParser
from app.models.company import CompanyInfo
from app.models.financial import FinancialData, CompanyData


class CompanyScraper(BaseScraper):
    """Scraper for company financial data"""

    def get_company_data(self, ticker: str) -> CompanyData:
        """
        Scrape all company data.

        Args:
            ticker: Company ticker symbol (e.g., RELIANCE)

        Returns:
            CompanyData object with all financial information
        """
        # Try consolidated first, fall back to standalone
        url = f"/company/{ticker}/consolidated/"

        try:
            response = self.get(url)
        except Exception:
            # Try without consolidated suffix
            url = f"/company/{ticker}/"
            response = self.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        company_info = self._parse_company_info(soup, ticker)
        quarterly_data = self._parse_quarterly_data(soup)
        annual_data = self._parse_annual_data(soup)
        cash_flow_data = self._parse_cash_flow_data(soup)

        # Merge cash flow data into annual data
        if cash_flow_data.periods:
            annual_data.cash_from_operations = cash_flow_data.cash_from_operations
            annual_data.cash_from_investing = cash_flow_data.cash_from_investing
            annual_data.cash_from_financing = cash_flow_data.cash_from_financing
            annual_data.net_cash_flow = cash_flow_data.net_cash_flow

        return CompanyData(
            company_info=company_info,
            quarterly_data=quarterly_data,
            annual_data=annual_data
        )

    def _parse_company_info(self, soup: BeautifulSoup, ticker: str) -> CompanyInfo:
        """
        Parse company information from the page header.

        Args:
            soup: BeautifulSoup object of the page
            ticker: Company ticker symbol

        Returns:
            CompanyInfo object
        """
        # Company name from h1
        name_elem = soup.select_one('h1.h2, h1')
        name = name_elem.get_text(strip=True) if name_elem else ticker

        # Current price - look for the price element specifically, not market cap
        current_price = None
        # Try specific price selectors first
        price_selectors = [
            '#top .flex-column .number:first-of-type',  # First number in the company header
            '.company-price .number',
            '.current-price'
        ]
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                current_price = self._parse_number(price_elem.get_text())
                if current_price:
                    break

        # Fallback: extract price from page text pattern "₹ 320 2.12%"
        if not current_price:
            page_text = soup.get_text(' ', strip=True)
            price_match = re.search(r'₹\s*([\d,]+(?:\.\d+)?)\s*[+-]?\d+\.?\d*\s*%', page_text)
            if price_match:
                current_price = self._parse_number(price_match.group(1))

        # Price change percentage
        change_elem = soup.select_one('.change, .price-change')
        price_change = None
        if change_elem:
            change_text = change_elem.get_text(strip=True)
            price_change = self._parse_percentage(change_text)

        # Key ratios from the ratios list
        ratios = self._parse_ratios(soup)

        # BSE/NSE codes
        bse_code = None
        nse_code = None
        code_elems = soup.select('.company-links a, .sub a')
        for elem in code_elems:
            href = elem.get('href', '')
            if 'bseindia' in href:
                bse_match = re.search(r'scrip_cd=(\d+)', href)
                if bse_match:
                    bse_code = bse_match.group(1)
            elif 'nseindia' in href:
                nse_code = ticker

        # Always calculate P/B ratio from current price and book value
        book_value = self._parse_number(ratios.get('book_value', ''))
        pb_ratio = None
        if current_price and book_value and book_value > 0:
            pb_ratio = round(current_price / book_value, 2)

        # Format debt value (lowercase key)
        debt_val = ratios.get('debt')
        if debt_val:
            debt_num = self._parse_number(debt_val)
            if debt_num is not None:
                if debt_num >= 100:
                    debt_val = f"₹{debt_num:,.0f} Cr"
                else:
                    debt_val = f"₹{debt_num:,.2f} Cr"

        return CompanyInfo(
            name=name,
            ticker=ticker,
            current_price=current_price,
            price_change_percent=price_change,
            market_cap=ratios.get('market_cap'),
            pe_ratio=self._parse_number(ratios.get('pe_ratio', '')),
            pb_ratio=pb_ratio,
            roce=self._parse_number(ratios.get('roce', '')),
            roe=self._parse_number(ratios.get('roe', '')),
            debt=debt_val,
            debt_to_equity=self._parse_number(ratios.get('debt_to_equity', '')),
            bse_code=bse_code,
            nse_code=nse_code or ticker
        )

    def _parse_ratios(self, soup: BeautifulSoup) -> dict:
        """
        Parse key ratios from the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of ratio name to value
        """
        ratios = {}

        # Try multiple selectors for ratio items
        ratio_items = soup.select('#top-ratios li, .company-ratios li, .ratios li, ul.ratios li, #top li')

        for item in ratio_items:
            # Try different element structures
            name_elem = item.select_one('.name, span.name')
            value_elem = item.select_one('.value, .number, span.number')

            if name_elem and value_elem:
                name = name_elem.get_text(strip=True).lower()
                value = value_elem.get_text(strip=True)

                if 'market cap' in name:
                    ratios['market_cap'] = value
                elif 'stock p/e' in name:
                    ratios['pe_ratio'] = value
                elif 'book value' in name and 'price' not in name:
                    ratios['book_value'] = value
                elif name == 'roce' or name == 'roce %':
                    ratios['roce'] = value
                elif name == 'roe' or name == 'roe %':
                    ratios['roe'] = value
                elif 'debt to equity' in name or name == 'debt/equity':
                    ratios['debt_to_equity'] = value
                elif name == 'debt':
                    ratios['debt'] = value

        # Get page text for regex extraction
        page_text = soup.get_text(' ', strip=True)

        # Extract Market Cap if not found
        if 'market_cap' not in ratios:
            mc_match = re.search(r'Market\s*Cap[:\s₹]*([\d,]+\.?\d*)\s*Cr', page_text, re.I)
            if mc_match:
                ratios['market_cap'] = f"₹ {mc_match.group(1)} Cr."

        # Extract P/E if not found
        if 'pe_ratio' not in ratios:
            pe_match = re.search(r'Stock\s*P/E[:\s]*(\d+\.?\d*)', page_text, re.I)
            if pe_match:
                ratios['pe_ratio'] = pe_match.group(1)

        # Extract Book Value first - format is "Book Value ₹ 670"
        if 'book_value' not in ratios:
            bv_match = re.search(r'Book\s+Value\s+₹?\s*(\d[\d,]*\.?\d*)', page_text, re.I)
            if bv_match:
                ratios['book_value'] = bv_match.group(1).replace(',', '')

        # P/B is calculated from current_price / book_value in _parse_company_info
        # No need to extract it from text

        # Extract ROCE - format is "ROCE 40.0 %"
        if 'roce' not in ratios:
            roce_match = re.search(r'ROCE\s+(\d+\.?\d*)\s*%', page_text)
            if roce_match:
                ratios['roce'] = roce_match.group(1)

        # Extract ROE - format is "ROE 32.8 %"
        if 'roe' not in ratios:
            # Use word boundary to avoid matching CROE
            roe_match = re.search(r'\bROE\s+(\d+\.?\d*)\s*%', page_text)
            if roe_match:
                ratios['roe'] = roe_match.group(1)

        # Extract Debt to Equity
        if 'debt_to_equity' not in ratios:
            de_match = re.search(r'Debt\s*to\s*equity[:\s]*(\d+\.?\d*)', page_text, re.I)
            if de_match:
                ratios['debt_to_equity'] = de_match.group(1)

        # Extract Borrowings/Debt from balance sheet section first
        # Format is "Borrowings + 94 82 80 ... 671 1,389" - need to get the LAST number
        balance_section = soup.select_one('#balance-sheet')
        if balance_section and 'debt' not in ratios:
            bs_text = balance_section.get_text(' ', strip=True)
            # Look for Borrowings row and capture all numbers after it
            borrowings_match = re.search(r'Borrowings\s*\+?\s*([\d,\s]+?)(?=\s*(?:Other|Trade|Total|$|\n))', bs_text)
            if borrowings_match:
                # Get all numbers from the row and take the last one (most recent)
                numbers = re.findall(r'[\d,]+', borrowings_match.group(1))
                if numbers:
                    ratios['debt'] = numbers[-1].replace(',', '')

            # Also try to get Equity for D/E calculation
            # Equity = Equity Capital + Reserves (both show with + sign and latest value)
            if 'debt' in ratios and 'debt_to_equity' not in ratios:
                try:
                    debt_val = float(ratios['debt'])
                    total_equity = 0.0

                    # Find Equity Capital value (last number in the row)
                    equity_cap_match = re.search(r'Equity\s+Capital\s*\+?\s*([\d,]+(?:\s+[\d,]+)*)', bs_text)
                    if equity_cap_match:
                        # Get all numbers and take the last one (most recent)
                        numbers = re.findall(r'[\d,]+', equity_cap_match.group(1))
                        if numbers:
                            total_equity += float(numbers[-1].replace(',', ''))

                    # Find Reserves value (last number in the row)
                    reserves_match = re.search(r'Reserves\s*\+?\s*([\d,]+(?:\s+[\d,]+)*)', bs_text)
                    if reserves_match:
                        numbers = re.findall(r'[\d,]+', reserves_match.group(1))
                        if numbers:
                            total_equity += float(numbers[-1].replace(',', ''))

                    if total_equity > 0:
                        ratios['debt_to_equity'] = str(round(debt_val / total_equity, 2))
                except (ValueError, TypeError):
                    pass

        # Fallback: try page-wide patterns for debt
        if 'debt' not in ratios:
            debt_patterns = [
                r'Borrowings\s*\+?\s*([\d,]+)',  # "Borrowings + 671"
                r'Debt\s+₹?\s*([\d,]+)\s*Cr',  # "Debt ₹ 1,389 Cr."
                r'Debt\s+(\d[\d,]*)',     # "Debt 1389"
            ]
            for pattern in debt_patterns:
                debt_match = re.search(pattern, page_text, re.I)
                if debt_match:
                    ratios['debt'] = debt_match.group(1).replace(',', '')
                    break

        return ratios

    def _parse_quarterly_data(self, soup: BeautifulSoup) -> FinancialData:
        """
        Parse quarterly results table.

        Args:
            soup: BeautifulSoup object

        Returns:
            FinancialData object
        """
        # Find the Quarterly Results section
        section = soup.find('section', id='quarters')
        if not section:
            # Try alternative selectors
            section = soup.find('section', {'id': re.compile(r'quarter', re.I)})

        if not section:
            self.logger.warning("Quarterly data section not found")
            return self._empty_financial_data()

        table = section.find('table')
        return TableParser.parse_financial_table(table) if table else self._empty_financial_data()

    def _parse_annual_data(self, soup: BeautifulSoup) -> FinancialData:
        """
        Parse annual Profit & Loss table.

        Args:
            soup: BeautifulSoup object

        Returns:
            FinancialData object
        """
        # Find the Profit & Loss section
        section = soup.find('section', id='profit-loss')
        if not section:
            # Try alternative selectors
            section = soup.find('section', {'id': re.compile(r'profit.*loss', re.I)})

        if not section:
            self.logger.warning("Annual data section not found")
            return self._empty_financial_data()

        table = section.find('table')
        return TableParser.parse_financial_table(table) if table else self._empty_financial_data()

    def _parse_cash_flow_data(self, soup: BeautifulSoup) -> FinancialData:
        """
        Parse cash flow statement table.

        Args:
            soup: BeautifulSoup object

        Returns:
            FinancialData object with cash flow data
        """
        # Find the Cash Flow section
        section = soup.find('section', id='cash-flow')
        if not section:
            # Try alternative selectors
            section = soup.find('section', {'id': re.compile(r'cash.*flow', re.I)})

        if not section:
            self.logger.warning("Cash flow section not found")
            return self._empty_financial_data()

        table = section.find('table')
        return TableParser.parse_financial_table(table) if table else self._empty_financial_data()

    def _parse_number(self, text: Optional[str]) -> Optional[float]:
        """
        Parse a number from text.

        Args:
            text: Text containing a number

        Returns:
            Float value or None
        """
        if not text:
            return None

        # Remove currency symbols, commas, whitespace, percentage signs, and "Cr"
        cleaned = re.sub(r'[₹,%\s]', '', str(text))
        cleaned = cleaned.replace(',', '').replace('Cr', '').replace('cr', '').strip()

        # Extract just the number
        match = re.search(r'([+-]?\d+\.?\d*)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _parse_percentage(self, text: Optional[str]) -> Optional[float]:
        """
        Parse a percentage value.

        Args:
            text: Text containing a percentage

        Returns:
            Float value or None
        """
        if not text:
            return None

        # Extract number from percentage text
        match = re.search(r'([+-]?\d+\.?\d*)\s*%?', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _empty_financial_data(self) -> FinancialData:
        """Return empty financial data structure"""
        return FinancialData(
            periods=[],
            sales=[],
            expenses=[],
            material_cost=[],
            operating_profit=[],
            opm_percent=[],
            other_income=[],
            interest=[],
            depreciation=[],
            profit_before_tax=[],
            tax_percent=[],
            net_profit=[],
            eps=[],
            cash_from_operations=[],
            cash_from_investing=[],
            cash_from_financing=[],
            net_cash_flow=[]
        )
