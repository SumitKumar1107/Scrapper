from typing import List
import re
from .base import BaseScraper
from app.models.company import SearchResult


class SearchScraper(BaseScraper):
    """Scraper for company search/autocomplete"""

    SEARCH_ENDPOINT = "/api/company/search/"

    def search(self, query: str) -> List[SearchResult]:
        """
        Search for companies matching the query.

        Args:
            query: Search query string (min 2 characters)

        Returns:
            List of matching companies
        """
        if len(query) < 2:
            return []

        try:
            data = self.get_json(self.SEARCH_ENDPOINT, params={'q': query})

            results = []
            for item in data:
                ticker = self._extract_ticker(item.get('url', ''))
                if ticker:
                    results.append(SearchResult(
                        id=item.get('id', 0),
                        name=item.get('name', ''),
                        ticker=ticker,
                        url=item.get('url', '')
                    ))

            return results

        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return []

    def _extract_ticker(self, url: str) -> str:
        """
        Extract ticker symbol from URL.

        Args:
            url: URL like /company/RELIANCE/consolidated/

        Returns:
            Ticker symbol (e.g., RELIANCE)
        """
        match = re.search(r'/company/([^/]+)/?', url)
        return match.group(1) if match else ''
