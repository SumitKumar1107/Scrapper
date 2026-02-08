from pydantic import BaseModel
from typing import Optional


class CompanyInfo(BaseModel):
    """Company basic information and key ratios"""
    name: str
    ticker: str
    current_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    market_cap: Optional[str] = None
    pe_ratio: Optional[float] = None
    book_value: Optional[float] = None
    dividend_yield: Optional[float] = None
    roce: Optional[float] = None
    roe: Optional[float] = None
    bse_code: Optional[str] = None
    nse_code: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


class SearchResult(BaseModel):
    """Search result item"""
    id: int
    name: str
    ticker: str
    url: str
