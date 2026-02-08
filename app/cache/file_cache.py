import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path
import hashlib
import logging


class FileCache:
    """File-based JSON caching with TTL support"""

    def __init__(self, cache_dir: str = "cache_data", ttl_hours: int = 24):
        """
        Initialize the file cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours for cached data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.logger = logging.getLogger(__name__)

    def _get_cache_path(self, key: str) -> Path:
        """
        Generate cache file path from key.

        Args:
            key: Cache key

        Returns:
            Path object for the cache file
        """
        # Use hash for safe filenames
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[dict]:
        """
        Retrieve cached data if valid.

        Args:
            key: Cache key

        Returns:
            Cached data dict or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            self.logger.debug(f"Cache miss for key: {key}")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check expiration
            cached_at = datetime.fromisoformat(cached['_cached_at'])
            if datetime.now() - cached_at > self.ttl:
                self.logger.info(f"Cache expired for key: {key}")
                cache_path.unlink()  # Delete expired cache
                return None

            self.logger.debug(f"Cache hit for key: {key}")
            return cached['data']

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Cache read error for key {key}: {e}")
            # Delete corrupted cache file
            try:
                cache_path.unlink()
            except Exception:
                pass
            return None

    def set(self, key: str, data: Any) -> None:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
        """
        cache_path = self._get_cache_path(key)

        cached = {
            '_cached_at': datetime.now().isoformat(),
            '_expires_at': (datetime.now() + self.ttl).isoformat(),
            '_key': key,
            'data': data
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached, f, indent=2, default=str)
            self.logger.info(f"Cached data for key: {key}")
        except IOError as e:
            self.logger.error(f"Cache write error for key {key}: {e}")

    def invalidate(self, key: str) -> bool:
        """
        Remove cached data.

        Args:
            key: Cache key

        Returns:
            True if cache was removed, False otherwise
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            self.logger.info(f"Invalidated cache for key: {key}")
            return True
        return False

    def clear_all(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to delete cache file {cache_file}: {e}")
        self.logger.info(f"Cleared {count} cache files")
        return count

    def get_cache_info(self, key: str) -> Optional[dict]:
        """
        Get cache metadata without returning data.

        Args:
            key: Cache key

        Returns:
            Dict with cached_at and expires_at, or None
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            return {
                'cached_at': cached.get('_cached_at'),
                'expires_at': cached.get('_expires_at')
            }
        except Exception:
            return None
