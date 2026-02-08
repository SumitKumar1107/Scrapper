from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .company import CompanyInfo


class FinancialData(BaseModel):
    """Financial metrics data for a time period"""
    periods: List[str] = []
    sales: List[Optional[float]] = []
    expenses: List[Optional[float]] = []
    operating_profit: List[Optional[float]] = []
    opm_percent: List[Optional[float]] = []
    other_income: List[Optional[float]] = []
    interest: List[Optional[float]] = []
    depreciation: List[Optional[float]] = []
    profit_before_tax: List[Optional[float]] = []
    tax_percent: List[Optional[float]] = []
    net_profit: List[Optional[float]] = []
    eps: List[Optional[float]] = []


class CompanyData(BaseModel):
    """Complete company data with financial metrics"""
    company_info: CompanyInfo
    quarterly_data: FinancialData
    annual_data: FinancialData
    cached_at: Optional[datetime] = None
    cache_expires_at: Optional[datetime] = None
