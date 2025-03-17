import logging
import time
import random
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from urllib.parse import quote, urlencode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaMarktScraper:
    def __init__(self):
        """Initialize the MediaMarkt scraper with Selenium."""
        # Set up Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the driver with webdriver_manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
        
        # Create debug directory
        self.debug_dir = 'debug'
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            logger.info(f"Created debug directory: {self.debug_dir}")

    def _random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay between actions to avoid detection."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text."""
        try:
            if not price_text:
                return None
            # Remove currency symbols and convert to float
            price = ''.join(filter(str.isdigit, price_text.replace(',', '.')))
            return float(price) / 100  # Convert cents to euros
        except (ValueError, AttributeError):
            return None

    def _build_search_url(self, query: str) -> str:
        """Build MediaMarkt search URL."""
        return f'https://www.mediamarkt.nl/nl/search.html?query={quote(query)}'

    def search(self, 
              query: str, 
              max_results: int = 20,
              sort_by: str = None) -> List[Dict[str, Any]]:
        """
        Search for products on MediaMarkt using Selenium.
        
        Args:
            query: Search query string
            max_results: Maximum number of products to return
            sort_by: Sort results by ('price_low_to_high', 'price_high_to_low', 'relevance')
            
        Returns:
            List of dictionaries containing product information
        """
        try:
            results = []
            
            # Build search URL
            search_url = self._build_search_url(query)
            
            # Add sorting if specified
            if sort_by:
                sort_params = {
                    'price_low_to_high': 'price-asc',
                    'price_high_to_low': 'price-desc',
                    'relevance': 'relevance'
                }
                if sort_by in sort_params:
                    search_url += f'&sort={sort_params[sort_by]}'
            
            # Navigate to search page
            logger.info(f"Navigating to: {search_url}")
            self.driver.get(search_url)
            
            # Wait for page to load
            self._random_sleep(2, 4)
            
            # Try different selectors for product containers
            selectors = [
                'div[class*="product-wrapper"]',
                'div[class*="product-tile"]',
                'div[class*="product-grid-item"]',
                'div[class*="product-item"]'
            ]
            
            product_containers = None
            for selector in selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    product_containers = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if product_containers:
                        logger.info(f"Found products with selector: {selector}")
                        break
                except TimeoutException:
                    logger.warning(f"Timeout with selector: {selector}")
                    continue
            
            if not product_containers:
                logger.error("No product containers found with any selector")
                # Save page source for debugging
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(self.debug_dir, f'mediamarkt_response_{timestamp}.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Saved page source to {debug_file}")
                return results
            
            # Process products
            for product in product_containers[:max_results]:
                try:
                    # Extract product information
                    title = product.find_element(By.CSS_SELECTOR, 'h2[class*="product-name"], a[class*="product-name"]').text.strip()
                    price_elem = product.find_element(By.CSS_SELECTOR, 'div[class*="price"], span[class*="price"]')
                    price = self._extract_price(price_elem.text.strip())
                    
                    # Get link
                    link_elem = product.find_element(By.CSS_SELECTOR, 'a[class*="product-link"], a[class*="product-name"]')
                    link = link_elem.get_attribute('href')
                    
                    # Get image URL
                    try:
                        image_elem = product.find_element(By.CSS_SELECTOR, 'img[class*="product-image"], img[class*="product-img"]')
                        image_url = image_elem.get_attribute('src')
                    except NoSuchElementException:
                        image_url = None
                    
                    # Get availability
                    try:
                        availability_elem = product.find_element(By.CSS_SELECTOR, 'div[class*="availability"], span[class*="availability"]')
                        availability_text = availability_elem.text.lower()
                        is_available = not any(x in availability_text for x in ['niet leverbaar', 'uitverkocht', 'tijdelijk uitverkocht'])
                    except NoSuchElementException:
                        is_available = True
                    
                    # Construct result
                    result = {
                        'title': title,
                        'price': f"{price:.2f}" if price else None,
                        'link': link,
                        'description': title,  # Use title as description
                        'store': 'MediaMarkt',
                        'image_url': image_url,
                        'available_online': is_available
                    }
                    
                    results.append(result)
                    logger.info(f"Added product: {result['title']} - €{result['price']}")
                    
                except Exception as e:
                    logger.error(f"Error processing product: {str(e)}")
                    continue
            
            logger.info(f"Found {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
        finally:
            # Clean up
            self.driver.quit() 