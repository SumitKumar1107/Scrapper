from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.scraper.search_scraper import SearchScraper
from app.models.company import SearchResult
from app.cache.file_cache import FileCache
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize scraper and cache
search_scraper = SearchScraper(delay=0.5)  # Shorter delay for search
cache = FileCache(ttl_hours=1)  # Short cache for search results


@router.get("/search", response_model=List[SearchResult])
async def search_companies(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)")
) -> List[SearchResult]:
    """
    Search for companies by name or ticker.

    Returns a list of matching companies for autocomplete.
    """
    query = q.strip().upper()
    cache_key = f"search:{query}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Search cache hit for: {query}")
        return [SearchResult(**item) for item in cached]

    try:
        # Perform search
        results = search_scraper.search(query)

        # Cache results
        if results:
            cache.set(cache_key, [r.model_dump() for r in results])

        return results

    except Exception as e:
        logger.error(f"Search error for '{query}': {e}")
        raise HTTPException(
            status_code=503,
            detail="Search service temporarily unavailable. Please try again."
        )
