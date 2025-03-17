from dataclasses import dataclass
from typing import Dict, Optional, Any
import os

@dataclass
class StoreConfig:
    name: str
    base_url: str
    search_url: str
    selectors: Dict[str, str]
    custom_headers: Optional[Dict[str, str]] = None
    custom_processing: Optional[Any] = None
    requires_ssl_verify: bool = True
    rate_limit: float = 0.5

# Common selectors used across stores
COMMON_SELECTORS = {
    'container': 'div[data-component-type="s-search-result"]',
    'title': 'h2 a span',
    'price': 'span.a-price-whole',
    'link': 'h2 a',
    'description': 'div.a-section.a-spacing-small'
}

# Store configurations
STORE_CONFIGS = {
    'amazon.nl': StoreConfig(
        name='Amazon',
        base_url='https://www.amazon.nl',
        search_url='https://www.amazon.nl/s?k={query}&language=en',
        selectors={},  # Not needed for API
        custom_headers={
            'AWS_ACCESS_KEY': os.getenv('AMAZON_ACCESS_KEY'),
            'AWS_SECRET_KEY': os.getenv('AMAZON_SECRET_KEY'),
            'ASSOCIATE_TAG': os.getenv('AMAZON_ASSOCIATE_TAG'),
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15'
        },
        requires_ssl_verify=True,
        rate_limit=1.0  # API has its own rate limits
    )
}

# Store categories
STORE_CATEGORIES = {
    'electronics': ['amazon.nl'],
    'gaming': ['amazon.nl'],
    'general': ['amazon.nl']
}

# Common headers used across stores
COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
} 