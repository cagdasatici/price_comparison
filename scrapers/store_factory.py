from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from queue import Queue
from threading import Lock

from .base.base_scraper import BaseScraper
from config.stores import STORE_CONFIGS, STORE_CATEGORIES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoreFactory:
    def __init__(self, max_workers: int = 8):
        """
        Initialize the store factory with a thread pool.
        
        Args:
            max_workers: Maximum number of concurrent threads (default: 8)
        """
        self.stores: Dict[str, BaseScraper] = {}
        self.max_workers = max_workers
        self._initialize_stores()
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize rate limiting
        self.rate_limit_queue = Queue()
        self.rate_limit_lock = Lock()
        
        # Initialize result collection
        self.results_lock = Lock()
        self.results: List[Dict[str, Any]] = []

    def _initialize_stores(self):
        """Initialize all store scrapers."""
        for store_id, config in STORE_CONFIGS.items():
            self.stores[store_id] = BaseScraper(config)

    def _rate_limit(self, store_id: str):
        """Implement rate limiting for store requests."""
        with self.rate_limit_lock:
            store = self.stores[store_id]
            if hasattr(store.store_config, 'rate_limit'):
                time.sleep(store.store_config.rate_limit)
            else:
                time.sleep(0.5)  # Default rate limit

    def _search_store_with_rate_limit(self, store_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Search a store with rate limiting."""
        try:
            self._rate_limit(store_id)
            return self.stores[store_id].search(query)
        except Exception as e:
            logger.error(f"Error searching {store_id}: {str(e)}")
            return None

    def search_store(self, store_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Search a specific store by ID."""
        if store_id not in self.stores:
            logger.error(f"Store not found: {store_id}")
            return None
            
        return self._search_store_with_rate_limit(store_id, query)

    def search_category(self, category: str, query: str) -> List[Dict[str, Any]]:
        """Search all stores in a specific category."""
        if category not in STORE_CATEGORIES:
            logger.error(f"Category not found: {category}")
            return []
            
        store_ids = STORE_CATEGORIES[category]
        return self._search_stores(store_ids, query)

    def search_all(self, query: str) -> List[Dict[str, Any]]:
        """Search all stores concurrently using thread pool."""
        self.results = []  # Reset results
        store_ids = list(self.stores.keys())
        return self._search_stores(store_ids, query)

    def _search_stores(self, store_ids: List[str], query: str) -> List[Dict[str, Any]]:
        """
        Search multiple stores concurrently with controlled concurrency.
        
        Args:
            store_ids: List of store IDs to search
            query: Search query
            
        Returns:
            List of search results
        """
        futures = []
        self.results = []

        # Submit tasks to thread pool
        for store_id in store_ids:
            future = self.executor.submit(
                self._search_store_with_rate_limit,
                store_id,
                query
            )
            futures.append((store_id, future))

        # Collect results as they complete
        for store_id, future in futures:
            try:
                result = future.result(timeout=30)  # 30 second timeout per store
                if result:
                    with self.results_lock:
                        self.results.append(result)
            except Exception as e:
                logger.error(f"Error getting result from {store_id}: {str(e)}")

        return self.results

    def get_store_categories(self) -> Dict[str, List[str]]:
        """Get all store categories and their stores."""
        return STORE_CATEGORIES

    def get_store_names(self) -> List[str]:
        """Get list of all store names."""
        return [config.name for config in STORE_CONFIGS.values()]

    def get_store_ids(self) -> List[str]:
        """Get list of all store IDs."""
        return list(STORE_CONFIGS.keys())

    def get_store_by_id(self, store_id: str) -> Optional[BaseScraper]:
        """Get store scraper by ID."""
        return self.stores.get(store_id)

    def get_store_by_name(self, store_name: str) -> Optional[BaseScraper]:
        """Get store scraper by name (case-insensitive)."""
        store_name = store_name.lower()
        for store_id, config in STORE_CONFIGS.items():
            if config.name.lower() == store_name:
                return self.stores[store_id]
        return None

    def __del__(self):
        """Cleanup thread pool on deletion."""
        self.executor.shutdown(wait=True) 