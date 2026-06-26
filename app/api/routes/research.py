from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import logging

from app.services.ai_research import (
    generate_research,
    generate_quarterly_research,
)
from app.cache.file_cache import FileCache
from app.models.financial import CompanyData
from app.scraper.company_scraper import CompanyScraper

router = APIRouter()
logger = logging.getLogger(__name__)

cache = FileCache(ttl_hours=24)
company_cache = FileCache(ttl_hours=24)
company_scraper = CompanyScraper(delay=1.5)


@router.get("/research/{ticker}")
async def get_research(
    ticker: str,
    company_name: str = Query(..., description="Full company name for AI analysis"),
    refresh: bool = Query(False, description="Force regenerate research")
):
    """
    Get AI-generated research analysis for a company.

    Uses Google Gemini to generate comprehensive stock research.
    Results are cached for 24 hours.
    """
    ticker = ticker.upper().strip()
    cache_key = f"research:{ticker}"

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Research cache hit for: {ticker}")
            return cached

    try:
        logger.info(f"Generating AI research for: {ticker} ({company_name})")
        analysis = generate_research(company_name)

        result = {
            "ticker": ticker,
            "company_name": company_name,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat(),
            "cache_expires_at": (
                datetime.now() + cache.ttl
            ).isoformat()
        }

        cache.set(cache_key, result)

        return result

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI research service is not configured. Please set GEMINI_API_KEY."
        )

    except FileNotFoundError as e:
        logger.error(f"Prompt template error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Research prompt template not found. Please check server configuration."
        )

    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"AI research error for {ticker}: {e}", exc_info=True)

        if '429' in str(e) or 'quota' in error_str or 'rate' in error_str:
            raise HTTPException(
                status_code=429,
                detail="API rate limit exceeded. Please wait a minute and try again."
            )

        raise HTTPException(
            status_code=503,
            detail="AI research generation failed. Please try again later."
        )


@router.get("/quarterly-research/{ticker}")
def get_quarterly_research(
    ticker: str,
    refresh: bool = Query(False, description="Force regenerate analysis")
):
    """Generate Gemini analysis of the latest available quarterly result."""
    ticker = ticker.upper().strip()
    cache_key = f"quarterly-research-v4:{ticker}"

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Quarterly research cache hit for: {ticker}")
            return cached

    try:
        company_data = None
        if not refresh:
            cached_company = company_cache.get(f"company:{ticker}")
            if cached_company:
                company_data = CompanyData.model_validate(cached_company)

        if company_data is None:
            company_data = company_scraper.get_company_data(ticker)

        company_name = company_data.company_info.name
        quarterly_data = company_data.quarterly_data.model_dump()
        analysis = generate_quarterly_research(
            ticker,
            company_name,
            quarterly_data
        )
        latest_period = (
            company_data.quarterly_data.periods[-1]
            if company_data.quarterly_data.periods
            else None
        )

        result = {
            "ticker": ticker,
            "company_name": company_name,
            "latest_period": latest_period,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat(),
            "cache_expires_at": (
                datetime.now() + cache.ttl
            ).isoformat()
        }
        cache.set(cache_key, result)
        return result

    except ValueError as e:
        logger.error(f"Quarterly research input/configuration error: {e}")
        if "GEMINI_API_KEY" in str(e):
            detail = (
                "AI research service is not configured. "
                "Please set GEMINI_API_KEY."
            )
            status_code = 503
        else:
            detail = str(e)
            status_code = 422
        raise HTTPException(status_code=status_code, detail=detail)

    except FileNotFoundError as e:
        logger.error(f"Quarterly prompt template error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Quarterly research prompt template was not found."
        )

    except Exception as e:
        error_str = str(e).lower()
        logger.error(
            f"Quarterly AI research error for {ticker}: {e}",
            exc_info=True
        )
        if '429' in str(e) or 'quota' in error_str or 'rate' in error_str:
            raise HTTPException(
                status_code=429,
                detail="API rate limit exceeded. Please wait and try again."
            )
        raise HTTPException(
            status_code=503,
            detail="Quarterly AI analysis failed. Please try again later."
        )
