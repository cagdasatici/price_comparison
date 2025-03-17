import logging
from typing import Dict, List, Optional, Any
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self, store_config, headless: bool = True):
        """
        Initialize Selenium scraper with Chrome browser.
        
        Args:
            store_config: Store configuration
            headless: Whether to run browser in headless mode
        """
        self.store_config = store_config
        
        # Initialize Chrome options
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--window-size=1920,1080')
        
        # Add custom user agent
        options.add_argument(f'user-agent={self.store_config.custom_headers["User-Agent"]}')
        
        # Initialize Chrome driver with webdriver_manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set page load timeout
        self.driver.set_page_load_timeout(30)
        
        # Initialize session with homepage visit
        self._init_session()

    def _random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Sleep for a random amount of time to simulate human behavior."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _human_like_scroll(self):
        """Perform human-like scrolling behavior."""
        # Get page height
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        
        # Scroll in random increments
        current_position = 0
        while current_position < page_height:
            # Random scroll amount between 100 and 300 pixels
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            
            # Scroll with random speed
            self.driver.execute_script(f"window.scrollTo(0, {current_position})")
            self._random_sleep(0.5, 1.5)
            
            # Occasionally scroll back up slightly
            if random.random() < 0.2:
                self.driver.execute_script(f"window.scrollTo(0, {current_position - random.randint(50, 150)})")
                self._random_sleep(0.3, 0.8)

    def _init_session(self):
        """Initialize session by visiting the homepage and performing human-like interactions."""
        try:
            logger.info(f"Visiting homepage: {self.store_config.base_url}")
            
            # Visit homepage
            self.driver.get(self.store_config.base_url)
            self._random_sleep(2, 4)  # Initial page load
            
            # Perform human-like scrolling
            self._human_like_scroll()
            
            # Accept cookies if present
            try:
                cookie_button = self.driver.find_element(By.ID, "sp-cc-accept")
                if cookie_button:
                    # Move to button with random delay
                    self._random_sleep(0.5, 1.0)
                    cookie_button.click()
                    self._random_sleep(1, 2)
            except:
                pass
            
            # Visit a few random pages to build up session history
            for _ in range(random.randint(2, 4)):
                try:
                    # Find random links
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    if links:
                        random_link = random.choice(links)
                        href = random_link.get_attribute('href')
                        if href and self.store_config.base_url in href:
                            self.driver.get(href)
                            self._random_sleep(1, 2)
                            self._human_like_scroll()
                except:
                    continue
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}")
            return False

    def extract_price(self, price_str: str) -> Optional[str]:
        """Extract numeric price from string."""
        if not price_str:
            return None
            
        try:
            # Remove currency symbols and spaces
            price_str = re.sub(r'[^\d.,]', '', price_str)
            
            # Handle different decimal separators
            if ',' in price_str and '.' in price_str:
                price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                price_str = price_str.replace(',', '.')
                
            price = float(price_str)
            return f"{price:.2f}"
        except (ValueError, TypeError):
            logger.warning(f"Failed to extract price from: {price_str}")
            return None

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for products using Selenium browser automation with human-like behavior.
        """
        try:
            # Construct search URL
            search_url = self.store_config.search_url.format(query=query)
            logger.info(f"Searching URL: {search_url}")
            
            # Navigate to search page
            self.driver.get(search_url)
            self._random_sleep(2, 4)
            
            # Perform human-like scrolling
            self._human_like_scroll()
            
            # Wait for results to load with increased timeout
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.s-result-item'))
                )
            except TimeoutException:
                logger.error("Timeout waiting for search results")
                with open('amazon_debug.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info("Saved page source to amazon_debug.html")
                return None
            
            # Additional wait for dynamic content
            self._random_sleep(2, 3)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Debug: Print title and check for common elements
            page_title = soup.find('title')
            logger.info(f"Page title: {page_title.text if page_title else 'No title found'}")
            
            # Check for captcha/robot check
            if 'robot' in self.driver.page_source.lower() or 'captcha' in self.driver.page_source.lower():
                logger.error("Detected anti-bot page")
                return None
            
            # Try different selectors with random delays
            logger.info("Trying to find product containers...")
            
            # Try original selector
            containers = soup.select(self.store_config.selectors['container'])
            logger.info(f"Found {len(containers)} containers with original selector")
            self._random_sleep(0.5, 1.0)
            
            # Try alternative selectors
            alt_containers = soup.find_all('div', class_='s-result-item')
            logger.info(f"Found {len(alt_containers)} containers with alternative selector")
            self._random_sleep(0.5, 1.0)
            
            # Try data-asin attribute
            asin_containers = soup.find_all(attrs={'data-asin': True})
            logger.info(f"Found {len(asin_containers)} containers with data-asin")
            
            # Find product container
            container = soup.select_one(self.store_config.selectors['container'])
            if not container:
                logger.warning("No product container found with primary selector")
                # Try alternative container
                container = next((c for c in alt_containers if c.get('data-asin')), None)
                if not container:
                    logger.warning("No product container found with alternative selector")
                    return None
                logger.info("Found container with alternative selector")
            
            # Random pause before extraction
            self._random_sleep(0.5, 1.0)
            
            # Extract product information with random delays
            try:
                # Extract title
                title_elem = container.select_one(self.store_config.selectors['title'])
                logger.info(f"Title element found: {title_elem is not None}")
                if not title_elem:
                    # Try alternative title selector
                    title_elem = container.select_one('.a-text-normal')
                    logger.info(f"Title element found with alternative selector: {title_elem is not None}")
                if not title_elem:
                    logger.warning("Title element not found")
                    return None
                title = title_elem.get_text(strip=True)
                logger.info(f"Found title: {title}")
                
                # Random pause
                self._random_sleep(0.3, 0.7)
                
                # Extract price
                price_elem = container.select_one(self.store_config.selectors['price'])
                logger.info(f"Price element found: {price_elem is not None}")
                if not price_elem:
                    # Try alternative price selector
                    price_elem = container.select_one('.a-price')
                    logger.info(f"Price element found with alternative selector: {price_elem is not None}")
                if not price_elem:
                    logger.warning("Price element not found")
                    return None
                price = self.extract_price(price_elem.get_text(strip=True))
                logger.info(f"Found price: {price}")
                if not price:
                    logger.warning("Failed to extract valid price")
                    return None
                
                # Random pause
                self._random_sleep(0.3, 0.7)
                
                # Extract link
                link_elem = container.select_one(self.store_config.selectors['link'])
                logger.info(f"Link element found: {link_elem is not None}")
                if not link_elem:
                    # Try alternative link selector
                    link_elem = container.select_one('a[href]')
                    logger.info(f"Link element found with alternative selector: {link_elem is not None}")
                if not link_elem:
                    logger.warning("Link element not found")
                    return None
                link = link_elem.get('href')
                if link and not link.startswith('http'):
                    link = f"{self.store_config.base_url.rstrip('/')}/{link.lstrip('/')}"
                logger.info(f"Found link: {link}")
                
                # Extract description
                desc_elem = container.select_one(self.store_config.selectors['description'])
                description = desc_elem.get_text(strip=True) if desc_elem else None
                logger.info(f"Found description: {description}")
                
                result = {
                    'title': title,
                    'price': price,
                    'link': link,
                    'description': description,
                    'store': self.store_config.name
                }
                logger.info(f"Successfully extracted product: {result}")
                return result
                
            except Exception as e:
                logger.error(f"Error extracting product information: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return None
        
    def __del__(self):
        """Clean up browser resources."""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error cleaning up browser: {str(e)}") 