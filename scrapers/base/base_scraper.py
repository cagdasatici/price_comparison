import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, store_config):
        self.store_config = store_config
        self.session = requests.Session()
        
        # Initialize cookies
        self.session.cookies.clear()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        # Update with store-specific headers
        if self.store_config.custom_headers:
            self.session.headers.update(self.store_config.custom_headers)
        
        # Configure session with retry strategy
        retry_strategy = requests.adapters.Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _init_session(self, url: str):
        """Initialize session with a visit to the homepage."""
        try:
            base_url = self.store_config.base_url
            logger.info(f"Initializing session with visit to {base_url}")
            
            # Visit homepage first
            response = self.session.get(
                base_url,
                verify=self.store_config.requires_ssl_verify,
                timeout=10
            )
            response.raise_for_status()
            
            # Small delay to mimic human behavior
            time.sleep(1.5)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}")
            return False

    def string_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def extract_price(self, price_str: str) -> Optional[str]:
        """Extract numeric price from string."""
        if not price_str:
            return None
            
        try:
            # Remove currency symbols and spaces
            price_str = re.sub(r'[^\d.,]', '', price_str)
            
            # Handle different decimal separators
            if ',' in price_str and '.' in price_str:
                # If both separators exist, assume European format
                price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                # If only comma exists, assume European format
                price_str = price_str.replace(',', '.')
                
            # Convert to float and back to string to validate
            price = float(price_str)
            return f"{price:.2f}"
        except (ValueError, TypeError):
            logger.warning(f"Failed to extract price from: {price_str}")
            return None

    def validate_price(self, price: float, product_type: str) -> bool:
        """Validate price based on product type."""
        try:
            if product_type == "console":
                return 300 <= price <= 600
            elif product_type == "game":
                return 20 <= price <= 80
            elif product_type == "accessory":
                return 10 <= price <= 100
            return True
        except (ValueError, TypeError):
            return False

    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and error handling."""
        try:
            # Initialize session if needed
            if 'amazon' in url.lower():
                self._init_session(url)
            
            # Add timeout to prevent hanging
            kwargs['timeout'] = kwargs.get('timeout', 10)
            
            # Add verify parameter if specified in config
            kwargs['verify'] = self.store_config.requires_ssl_verify
            
            # Make the request
            response = self.session.request(method, url, **kwargs)
            
            # Log response details for debugging
            logger.info(f"Request to {url} - Status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error for {url}: {str(e)}")
            return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error for {url}: {str(e)}")
            return None
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error for {url}: {str(e)}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during request to {url}: {str(e)}")
            return None

    def parse_product(self, element) -> Optional[Dict[str, Any]]:
        """Parse product information from HTML element."""
        try:
            # Extract title
            title_elem = element.find(self.store_config.selectors['title'])
            if not title_elem:
                logger.warning("Title element not found")
                return None
            title = title_elem.get_text(strip=True)

            # Extract price
            price_elem = element.find(self.store_config.selectors['price'])
            if not price_elem:
                logger.warning("Price element not found")
                return None
            price = self.extract_price(price_elem.get_text(strip=True))
            if not price:
                logger.warning("Failed to extract valid price")
                return None

            # Extract link
            link_elem = element.find(self.store_config.selectors['link'])
            if not link_elem:
                logger.warning("Link element not found")
                return None
            link = link_elem.get('href')
            if link and not link.startswith('http'):
                link = f"{self.store_config.base_url.rstrip('/')}/{link.lstrip('/')}"

            # Extract description
            desc_elem = element.find(self.store_config.selectors['description'])
            description = desc_elem.get_text(strip=True) if desc_elem else None

            return {
                'title': title,
                'price': price,
                'link': link,
                'description': description,
                'store': self.store_config.name
            }
        except Exception as e:
            logger.error(f"Error parsing product: {str(e)}")
            return None

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for products and return the best match."""
        try:
            # Encode query for URL
            encoded_query = quote(query)
            
            # Construct search URL
            search_url = self.store_config.search_url.format(query=encoded_query)
            
            # Make request
            response = self.make_request(search_url)
            if not response:
                logger.error(f"Failed to get response from {search_url}")
                return None
                
            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find product container
            container = soup.find(self.store_config.selectors['container'])
            if not container:
                logger.warning(f"No products found for query: {query}")
                return None
                
            # Parse product
            result = self.parse_product(container)
            if not result:
                logger.warning(f"Failed to parse product for query: {query}")
                return None
                
            # Validate price
            try:
                price = float(result['price'])
                if not self.validate_price(price, "console"):  # Default to console validation
                    logger.warning(f"Invalid price {price} for product: {result['title']}")
                    return None
            except (ValueError, TypeError):
                logger.warning(f"Failed to validate price for product: {result['title']}")
                return None
                
            return result
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return None 