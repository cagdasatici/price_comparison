import logging
from scrapers.base.base_scraper import BaseScraper
from config.stores import STORE_CONFIGS
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_amazon_scraper():
    # Get Amazon config
    amazon_config = STORE_CONFIGS.get('amazon.nl')
    if not amazon_config:
        logger.error("Amazon config not found!")
        return

    # Create scraper
    scraper = BaseScraper(amazon_config)
    
    # Test search
    query = "PlayStation 5"
    logger.info(f"Testing Amazon search for: {query}")
    
    # Make request directly to see response
    url = amazon_config.search_url.format(query=query)
    logger.info(f"Requesting URL: {url}")
    
    response = scraper.make_request(url)
    if response:
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response content length: {len(response.text)}")
        
        # Save response content for inspection
        with open('amazon_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Saved response to amazon_response.html")
        
        # Try to parse the response
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Look for common elements to check if we're getting a search page
        title = soup.find('title')
        logger.info(f"Page title: {title.text if title else 'No title found'}")
        
        # Check for captcha
        if 'captcha' in response.text.lower() or 'robot' in response.text.lower():
            logger.error("Detected possible CAPTCHA or anti-bot page!")
            return
        
        # Try to find any product-like elements
        all_divs = soup.find_all('div', class_='s-result-item')
        logger.info(f"Found {len(all_divs)} divs with class 's-result-item'")
        
        # Try the specific container selector
        container = soup.find(amazon_config.selectors['container'])
        if container:
            logger.info("Found product container!")
            result = scraper.parse_product(container)
            if result:
                logger.info(f"Successfully parsed product: {result}")
            else:
                logger.error("Failed to parse product from container")
        else:
            logger.error("No product container found in response")
            
            # Try alternative selectors
            alt_containers = soup.find_all('div', {'data-asin': True})
            if alt_containers:
                logger.info(f"Found {len(alt_containers)} alternative product containers")
                # Try parsing the first one
                result = scraper.parse_product(alt_containers[0])
                if result:
                    logger.info(f"Successfully parsed product using alternative container: {result}")
    else:
        logger.error("Failed to get response from Amazon")

if __name__ == "__main__":
    test_amazon_scraper() 