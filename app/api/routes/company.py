from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import requests
import logging

from app.scraper.company_scraper import CompanyScraper
from app.cache.file_cache import FileCache
from app.utils.exceptions import (
    CompanyNotFoundError,
    RateLimitError,
    ScrapingError,
    DataParsingError
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize scraper and cache
company_scraper = CompanyScraper(delay=1.5)  # 1.5 second delay between requests
cache = FileCache(ttl_hours=24)  # 24 hour cache for company data


@router.get("/company/{ticker}")
async def get_company_data(
    ticker: str,
    refresh: bool = Query(False, description="Force refresh cache")
):
    """
    Get company financial data.

    Returns company info, quarterly and annual financial data.
    """
    ticker = ticker.upper().strip()
    cache_key = f"company:{ticker}"

    # Check cache first (unless refresh requested)
    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for company: {ticker}")
            return cached

    try:
        # Scrape fresh data
        logger.info(f"Scraping data for company: {ticker}")
        data = company_scraper.get_company_data(ticker)

        # Convert to dict and add cache metadata
        data_dict = data.model_dump()
        data_dict['cached_at'] = datetime.now().isoformat()
        data_dict['cache_expires_at'] = (
            datetime.now() + cache.ttl
        ).isoformat()

        # Store in cache
        cache.set(cache_key, data_dict)

        return data_dict

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 404:
                logger.warning(f"Company not found: {ticker}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Company '{ticker}' not found. Please check the ticker symbol."
                )
            elif e.response.status_code == 429:
                logger.warning(f"Rate limited for: {ticker}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait a moment and try again."
                )

        logger.error(f"HTTP error for {ticker}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch data. The source might be temporarily unavailable."
        )

    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for {ticker}")
        raise HTTPException(
            status_code=503,
            detail="Network error. Please check your connection."
        )

    except requests.exceptions.Timeout:
        logger.error(f"Timeout for {ticker}")
        raise HTTPException(
            status_code=504,
            detail="Request timed out. Please try again."
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {ticker}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Network error. Please check your connection."
        )

    except Exception as e:
        logger.error(f"Unexpected error for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to parse financial data. Please try again later."
        )


@router.delete("/company/{ticker}/cache")
async def clear_company_cache(ticker: str):
    """
    Clear cached data for a specific company.
    """
    ticker = ticker.upper().strip()
    cache_key = f"company:{ticker}"

    if cache.invalidate(cache_key):
        return {"message": f"Cache cleared for {ticker}"}
    else:
        return {"message": f"No cache found for {ticker}"}
