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

        # Current price
        price_elem = soup.select_one('#top .number, .company-price .number, .current-price')
        current_price = self._parse_number(price_elem.get_text()) if price_elem else None

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

        return CompanyInfo(
            name=name,
            ticker=ticker,
            current_price=current_price,
            price_change_percent=price_change,
            market_cap=ratios.get('market_cap'),
            pe_ratio=self._parse_number(ratios.get('pe_ratio', '')),
            book_value=self._parse_number(ratios.get('book_value', '')),
            dividend_yield=self._parse_number(ratios.get('dividend_yield', '')),
            roce=self._parse_number(ratios.get('roce', '')),
            roe=self._parse_number(ratios.get('roe', '')),
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

        # Try different selectors for ratio items
        ratio_items = soup.select('#top-ratios li, .company-ratios li, .ratios li')

        for item in ratio_items:
            name_elem = item.select_one('.name, span:first-child')
            value_elem = item.select_one('.value, .number, span:last-child')

            if name_elem and value_elem:
                name = name_elem.get_text(strip=True).lower()
                value = value_elem.get_text(strip=True)

                if 'market cap' in name:
                    ratios['market_cap'] = value
                elif 'stock p/e' in name or 'p/e' in name:
                    ratios['pe_ratio'] = value
                elif 'book value' in name:
                    ratios['book_value'] = value
                elif 'dividend' in name:
                    ratios['dividend_yield'] = value
                elif 'roce' in name:
                    ratios['roce'] = value
                elif 'roe' in name:
                    ratios['roe'] = value

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

        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[₹,\s]', '', text)
        cleaned = cleaned.replace(',', '')

        try:
            return float(cleaned)
        except ValueError:
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
            operating_profit=[],
            opm_percent=[],
            other_income=[],
            interest=[],
            depreciation=[],
            profit_before_tax=[],
            tax_percent=[],
            net_profit=[],
            eps=[]
        )
