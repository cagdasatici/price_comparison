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

class AmazonScraper:
    def __init__(self):
        """Initialize the Amazon scraper with proper headers."""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
                debug_file = os.path.join(self.debug_dir, f'amazon_response_{timestamp}.html')
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
            # Remove currency symbols and convert to float
            price = ''.join(filter(str.isdigit, price_text.replace(',', '.')))
            return float(price)
        except (ValueError, AttributeError):
            return None

    def _extract_rating(self, rating_elem) -> Tuple[Optional[float], Optional[int]]:
        """Extract rating and review count."""
        try:
            if not rating_elem:
                return None, None
                
            # Get rating text (e.g., "4.6 van 5 sterren")
            rating_text = rating_elem.text.strip()
            if not rating_text:
                return None, None
                
            # Extract rating value
            rating = float(rating_text.split()[0].replace(',', '.'))
            
            # Extract review count
            review_count = 0
            review_text = rating_elem.find_next_sibling(text=True)
            if review_text:
                review_count = int(''.join(filter(str.isdigit, review_text)))
                
            return rating, review_count
        except (ValueError, AttributeError, IndexError):
            return None, None

    def _clean_description(self, text: str) -> str:
        """Clean up product description text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Split into parts by common separators
        parts = text.split("€")
        if parts:
            # Keep only the first part (usually the main description)
            text = parts[0].strip()
        return text

    def _get_high_res_image(self, url: str) -> str:
        """Convert image URL to high resolution version."""
        if not url:
            return None
        # Replace Amazon's size suffixes with larger versions
        return url.replace('._AC_UL320_', '._AC_SL1500_')

    def _build_search_url(self, query: str, page: int = 1, sort_by: str = None, min_price: float = None, max_price: float = None) -> str:
        """Build Amazon search URL with parameters."""
        params = {
            'k': query,
            'page': page
        }
        
        # Add sorting parameter
        if sort_by:
            sort_params = {
                'price_low_to_high': 'price-asc-rank',
                'price_high_to_low': 'price-desc-rank',
                'rating': 'review-rank',
                'newest': 'date-desc-rank'
            }
            if sort_by in sort_params:
                params['s'] = sort_params[sort_by]
        
        # Add price range parameters
        if min_price is not None:
            params['rh'] = f'p_36:{int(min_price*100)}00-'
        if max_price is not None:
            if 'rh' in params:
                params['rh'] += f'{int(max_price*100)}00'
            else:
                params['rh'] = f'p_36:-{int(max_price*100)}00'
        
        url = f'https://www.amazon.nl/s?{urlencode(params)}'
        logger.info(f"Built search URL: {url}")
        return url

    def search(self, 
              query: str, 
              max_results: int = 20,
              sort_by: str = None,
              min_price: float = None,
              max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon.
        
        Args:
            query: Search query string
            max_results: Maximum number of products to return
            sort_by: Sort results by ('price_low_to_high', 'price_high_to_low', 'rating', 'newest')
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of dictionaries containing product information
        """
        try:
            results = []
            page = 1
            
            while len(results) < max_results and page <= 5:  # Limit to 5 pages to avoid too many requests
                url = self._build_search_url(query, page, sort_by, min_price, max_price)
                logger.info(f"Searching Amazon for: {query} (page {page})")
                
                html = self._make_request(url)
                if not html:
                    logger.error("Failed to get HTML response")
                    break
                    
                soup = BeautifulSoup(html, 'lxml')
                
                # Log page title and other metadata
                logger.info(f"Page title: {soup.title.string if soup.title else 'No title found'}")
                
                # Look for all product containers
                products = soup.select('div[data-component-type="s-search-result"]') or soup.select('.s-result-item')
                logger.info(f"Found {len(products)} product containers on page {page}")
                
                if not products:
                    logger.error("No products found on page")
                    break

                for product in products:
                    if len(results) >= max_results:
                        break
                        
                    try:
                        # Extract product information with updated selectors
                        title_elem = product.select_one('h2 a span') or product.select_one('.a-text-normal')
                        price_elem = product.select_one('span.a-price-whole') or product.select_one('.a-price .a-offscreen')
                        link_elem = product.select_one('h2 a') or product.select_one('.a-link-normal')
                        description_elem = product.select_one('div.a-section.a-spacing-small') or product.select_one('.a-color-secondary')
                        image_elem = product.select_one('img.s-image') or product.select_one('.s-image')
                        rating_elem = product.select_one('i.a-icon-star-small') or product.select_one('.a-icon-star')
                        
                        if not all([title_elem, price_elem, link_elem]):
                            logger.warning("Missing required product elements")
                            continue
                        
                        # Extract and validate price
                        price = self._extract_price(price_elem.text)
                        if not price:
                            logger.warning("Failed to extract price")
                            continue
                            
                        # Apply price filters
                        if min_price and price < min_price:
                            continue
                        if max_price and price > max_price:
                            continue

                        # Get rating information
                        rating, review_count = self._extract_rating(rating_elem)
                        
                        # Get image URL and convert to high resolution
                        image_url = image_elem.get('src') if image_elem else None
                        high_res_image = self._get_high_res_image(image_url)
                        
                        # Construct result
                        result = {
                            'title': title_elem.text.strip(),
                            'price': f"{price:.2f}",
                            'link': f"https://www.amazon.nl{link_elem['href']}" if link_elem.get('href', '').startswith('/') else link_elem['href'],
                            'description': self._clean_description(description_elem.text if description_elem else ''),
                            'store': 'Amazon',
                            'image_url': image_url,
                            'high_res_image_url': high_res_image,
                            'rating': rating,
                            'review_count': review_count
                        }
                        
                        results.append(result)
                        logger.info(f"Added product: {result['title']} - €{result['price']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing product: {str(e)}")
                        continue
                
                page += 1
            
            # Sort results if needed
            if sort_by:
                if sort_by == 'price_low_to_high':
                    results.sort(key=lambda x: float(x['price']))
                elif sort_by == 'price_high_to_low':
                    results.sort(key=lambda x: float(x['price']), reverse=True)
                elif sort_by == 'rating' and all(x['rating'] for x in results):
                    results.sort(key=lambda x: x['rating'], reverse=True)
            
            logger.info(f"Found {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return [] 