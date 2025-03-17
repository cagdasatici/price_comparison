import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarktplaatsScraper:
    def __init__(self):
        """Initialize the Marktplaats scraper with proper headers."""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
        
        # Create debug directory
        self.debug_dir = 'debug'
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            logger.info(f"Created debug directory: {self.debug_dir}")

    def _random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay between requests to avoid detection."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _make_request(self, url: str) -> Optional[str]:
        """Make a request with retry logic and error handling."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._random_sleep()
                logger.info(f"Making request to: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Save HTML response for debugging
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(self.debug_dir, f'marktplaats_response_{timestamp}.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Saved HTML response to {debug_file}")
                
                # Log response details
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                return response.text
            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        return None

    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        try:
            if price_text.lower() == 'bieden':
                return None
            # Remove currency symbols and convert to float
            price = ''.join(filter(str.isdigit, price_text.replace(',', '.')))
            return float(price)
        except (ValueError, AttributeError):
            return None

    def _clean_description(self, text: str) -> str:
        """Clean up product description text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = " ".join(text.split())
        return text

    def _build_search_url(self, query: str, page: int = 1, distance: Optional[int] = None, min_price: Optional[float] = None, max_price: Optional[float] = None) -> str:
        """Build Marktplaats search URL with parameters."""
        params = {
            'q': query,
            'page': page
        }
        
        # Add distance parameter if specified
        if distance:
            params['distanceMeters'] = distance * 1000  # Convert km to meters
        
        # Add price range parameters
        if min_price is not None:
            params['priceFrom'] = int(min_price)
        if max_price is not None:
            params['priceTo'] = int(max_price)
        
        url = f'https://www.marktplaats.nl/q/{quote(query)}/'
        if len(params) > 1:  # If we have more parameters than just the query
            url += f'?{urlencode(params)}'
            
        logger.info(f"Built search URL: {url}")
        return url

    def search(self, 
              query: str, 
              max_results: int = 20,
              distance: Optional[int] = None,
              min_price: Optional[float] = None,
              max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for products on Marktplaats.
        
        Args:
            query: Search query string
            max_results: Maximum number of products to return
            distance: Maximum distance in kilometers
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of dictionaries containing product information
        """
        try:
            results = []
            page = 1
            
            while len(results) < max_results and page <= 5:  # Limit to 5 pages
                url = self._build_search_url(query, page, distance, min_price, max_price)
                logger.info(f"Searching Marktplaats for: {query} (page {page})")
                
                html = self._make_request(url)
                if not html:
                    logger.error("Failed to get HTML response")
                    break
                    
                soup = BeautifulSoup(html, 'lxml')
                
                # Log page title
                logger.info(f"Page title: {soup.title.string if soup.title else 'No title found'}")
                
                # Look for all product containers
                products = soup.select('article[data-test="advertisement-item"]')
                logger.info(f"Found {len(products)} product containers on page {page}")
                
                if not products:
                    logger.error("No products found on page")
                    break

                for product in products:
                    if len(results) >= max_results:
                        break
                        
                    try:
                        # Extract product information
                        title_elem = product.select_one('h3.mp-Listing-title')
                        price_elem = product.select_one('span.mp-Listing-price')
                        link_elem = product.select_one('a.mp-Listing-coverLink')
                        description_elem = product.select_one('p.mp-Listing-description')
                        image_elem = product.select_one('img.mp-Listing-image')
                        location_elem = product.select_one('span.mp-Listing-location')
                        seller_elem = product.select_one('span.mp-Listing-seller')
                        condition_elem = product.select_one('span.mp-Listing-attributes')
                        
                        if not all([title_elem, link_elem]):
                            logger.warning("Missing required product elements")
                            continue
                        
                        # Extract price (handle "Bieden" case)
                        price_text = price_elem.text.strip() if price_elem else "Bieden"
                        price = self._extract_price(price_text)
                        
                        # Apply price filters
                        if min_price and (not price or price < min_price):
                            continue
                        if max_price and (not price or price > max_price):
                            continue
                        
                        # Construct result
                        result = {
                            'title': title_elem.text.strip(),
                            'price': f"{price:.2f}" if price else price_text,
                            'link': f"https://www.marktplaats.nl{link_elem['href']}" if link_elem.get('href', '').startswith('/') else link_elem['href'],
                            'description': self._clean_description(description_elem.text if description_elem else ''),
                            'store': 'Marktplaats',
                            'image_url': image_elem.get('src') if image_elem else None,
                            'location': location_elem.text.strip() if location_elem else None,
                            'seller': seller_elem.text.strip() if seller_elem else None,
                            'condition': condition_elem.text.strip() if condition_elem else None
                        }
                        
                        results.append(result)
                        logger.info(f"Added product: {result['title']} - {result['price']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing product: {str(e)}")
                        continue
                
                page += 1
            
            logger.info(f"Found {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return [] 