from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict
import re
from app.models.financial import FinancialData


class TableParser:
    """Parser for financial data tables"""

    # Mapping of row labels to model fields
    ROW_MAPPING = {
        'sales': 'sales',
        'revenue': 'sales',
        'expenses': 'expenses',
        'raw material': 'material_cost',
        'material cost': 'material_cost',
        'cost of materials consumed': 'material_cost',
        'material consumed': 'material_cost',
        'operating profit': 'operating_profit',
        'opm': 'opm_percent',
        'other income': 'other_income',
        'interest': 'interest',
        'depreciation': 'depreciation',
        'profit before tax': 'profit_before_tax',
        'tax': 'tax_percent',
        'net profit': 'net_profit',
        'eps in rs': 'eps',
        'eps': 'eps',
        # Cash flow mappings
        'cash from operating': 'cash_from_operations',
        'cash from investing': 'cash_from_investing',
        'cash from financing': 'cash_from_financing',
        'net cash flow': 'net_cash_flow',
    }

    @classmethod
    def parse_financial_table(cls, table: Tag) -> FinancialData:
        """
        Parse a financial data table.

        Args:
            table: BeautifulSoup Tag object representing the table

        Returns:
            FinancialData object with parsed values
        """
        if not table:
            return cls._empty_data()

        # Get periods from header row
        periods = cls._parse_header(table)

        # Initialize data dict with empty lists
        data = {field: [None] * len(periods) for field in set(cls.ROW_MAPPING.values())}

        # Parse each data row
        rows = table.select('tbody tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # First cell is the row label
            label_cell = cells[0]
            label = label_cell.get_text(strip=True)
            # Remove trailing + or other markers
            label = re.sub(r'\s*\+$', '', label).strip().lower()

            # Find matching field
            field = None
            for key, field_name in cls.ROW_MAPPING.items():
                if key in label:
                    field = field_name
                    break

            if field:
                # Parse values from remaining cells (skip first column which is label)
                values = []
                for cell in cells[1:]:
                    text = cell.get_text(strip=True)
                    value = cls._parse_cell_value(text)
                    values.append(value)

                # Trim to match period count (exclude TTM if present)
                data[field] = values[:len(periods)]

        return FinancialData(
            periods=periods,
            sales=data.get('sales', []),
            expenses=data.get('expenses', []),
            material_cost=data.get('material_cost', []),
            operating_profit=data.get('operating_profit', []),
            opm_percent=data.get('opm_percent', []),
            other_income=data.get('other_income', []),
            interest=data.get('interest', []),
            depreciation=data.get('depreciation', []),
            profit_before_tax=data.get('profit_before_tax', []),
            tax_percent=data.get('tax_percent', []),
            net_profit=data.get('net_profit', []),
            eps=data.get('eps', []),
            cash_from_operations=data.get('cash_from_operations', []),
            cash_from_investing=data.get('cash_from_investing', []),
            cash_from_financing=data.get('cash_from_financing', []),
            net_cash_flow=data.get('net_cash_flow', [])
        )

    @classmethod
    def _parse_header(cls, table: Tag) -> List[str]:
        """
        Parse period headers from table.

        Args:
            table: BeautifulSoup Tag object

        Returns:
            List of period strings (e.g., ['Mar 2020', 'Mar 2021', ...])
        """
        header_row = table.select_one('thead tr')
        if not header_row:
            return []

        periods = []
        headers = header_row.find_all('th')

        for th in headers[1:]:  # Skip first column (label column)
            period = th.get_text(strip=True)
            # Skip TTM (Trailing Twelve Months) column
            if period and period.upper() != 'TTM':
                periods.append(period)

        return periods

    @classmethod
    def _parse_cell_value(cls, text: str) -> Optional[float]:
        """
        Parse a numeric value from cell text.

        Args:
            text: Cell text content

        Returns:
            Float value or None if not parseable
        """
        if not text or text == '-' or text == '':
            return None

        # Remove commas, percentage signs, and whitespace
        cleaned = re.sub(r'[,%\s]', '', text)
        cleaned = cleaned.replace(',', '')

        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def _empty_data(cls) -> FinancialData:
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
