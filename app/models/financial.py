from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .company import CompanyInfo


class FinancialData(BaseModel):
    """Financial metrics data for a time period"""
    periods: List[str] = []
    sales: List[Optional[float]] = []
    expenses: List[Optional[float]] = []
    material_cost: List[Optional[float]] = []  # For Gross Margin calculation
    operating_profit: List[Optional[float]] = []
    opm_percent: List[Optional[float]] = []
    other_income: List[Optional[float]] = []
    interest: List[Optional[float]] = []
    depreciation: List[Optional[float]] = []
    profit_before_tax: List[Optional[float]] = []
    tax_percent: List[Optional[float]] = []
    net_profit: List[Optional[float]] = []
    eps: List[Optional[float]] = []
    # Cash flow data
    cash_from_operations: List[Optional[float]] = []
    cash_from_investing: List[Optional[float]] = []
    cash_from_financing: List[Optional[float]] = []
    net_cash_flow: List[Optional[float]] = []


class ShareholdingData(BaseModel):
    """Shareholding pattern data for a time period"""
    periods: List[str] = []
    promoters: List[Optional[float]] = []
    fiis: List[Optional[float]] = []
    diis: List[Optional[float]] = []
    government: List[Optional[float]] = []
    public: List[Optional[float]] = []


class CompanyData(BaseModel):
    """Complete company data with financial metrics"""
    company_info: CompanyInfo
    quarterly_data: FinancialData
    annual_data: FinancialData
    shareholding_quarterly: Optional[ShareholdingData] = None
    shareholding_yearly: Optional[ShareholdingData] = None
    cached_at: Optional[datetime] = None
    cache_expires_at: Optional[datetime] = None
