from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request


class ScraperException(Exception):
    """Base exception for scraper errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CompanyNotFoundError(ScraperException):
    """Raised when company is not found"""

    def __init__(self, ticker: str):
        super().__init__(
            message=f"Company '{ticker}' not found. Please check the ticker symbol.",
            status_code=404
        )


class RateLimitError(ScraperException):
    """Raised when rate limited by source"""

    def __init__(self):
        super().__init__(
            message="Too many requests. Please wait a moment and try again.",
            status_code=429
        )


class ScrapingError(ScraperException):
    """Raised when scraping fails"""

    def __init__(self, message: str = "Failed to fetch data. The source might be temporarily unavailable."):
        super().__init__(message=message, status_code=503)


class DataParsingError(ScraperException):
    """Raised when data parsing fails"""

    def __init__(self, message: str = "Failed to parse financial data. Page structure may have changed."):
        super().__init__(message=message, status_code=500)


class CacheError(ScraperException):
    """Raised when cache operations fail"""

    def __init__(self, message: str = "Cache operation failed."):
        super().__init__(message=message, status_code=500)


async def scraper_exception_handler(request: Request, exc: ScraperException) -> JSONResponse:
    """
    Handle ScraperException and return JSON response.

    Args:
        request: FastAPI request
        exc: ScraperException instance

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )
