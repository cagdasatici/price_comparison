import logging
from scrapers.selenium_scraper import SeleniumScraper
from config.stores import STORE_CONFIGS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_selenium_scraper(headless: bool = True):
    # Get Amazon config
    amazon_config = STORE_CONFIGS.get('amazon.nl')
    if not amazon_config:
        logger.error("Amazon config not found!")
        return

    try:
        # Create scraper in headless mode
        scraper = SeleniumScraper(amazon_config, headless=headless)
        
        # Test search
        query = "PlayStation 5"
        logger.info(f"Testing Amazon search for: {query}")
        
        # Perform search
        result = scraper.search(query)
        
        if result:
            logger.info("Search successful!")
            logger.info(f"Found product: {result}")
        else:
            logger.error("No results found")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    finally:
        # Clean up
        if 'scraper' in locals():
            del scraper

if __name__ == "__main__":
    # Run in headless mode by default
    test_selenium_scraper(headless=True) 