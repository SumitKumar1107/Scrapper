import requests
import time
from typing import Optional
import logging


class BaseScraper:
    """Base scraper with rate limiting and session management"""

    BASE_URL = "https://www.screener.in"

    def __init__(self, delay: float = 1.5):
        """
        Initialize the scraper.

        Args:
            delay: Minimum delay between requests in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.delay = delay
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """
        Make a rate-limited GET request.

        Args:
            url: URL path (will be appended to BASE_URL if starts with /)
            params: Optional query parameters

        Returns:
            Response object

        Raises:
            requests.RequestException: If request fails
        """
        self._rate_limit()

        full_url = f"{self.BASE_URL}{url}" if url.startswith('/') else url

        try:
            self.logger.info(f"Fetching: {full_url}")
            response = self.session.get(full_url, params=params, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {full_url}: {e}")
            raise

    def get_json(self, url: str, params: Optional[dict] = None) -> dict:
        """
        Make a rate-limited GET request and return JSON.

        Args:
            url: URL path
            params: Optional query parameters

        Returns:
            Parsed JSON response
        """
        response = self.get(url, params)
        return response.json()
