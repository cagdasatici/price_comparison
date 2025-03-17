import logging
import os
from scrapers.amazon_api_scraper import AmazonAPIScraper
from config.stores import STORE_CONFIGS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_amazon_api_scraper():
    # Check for required environment variables
    required_vars = ['AMAZON_ACCESS_KEY', 'AMAZON_SECRET_KEY', 'AMAZON_ASSOCIATE_TAG']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please set these environment variables before running the test")
        return

    # Get Amazon config
    amazon_config = STORE_CONFIGS.get('amazon.nl')
    if not amazon_config:
        logger.error("Amazon config not found!")
        return

    try:
        # Create scraper
        scraper = AmazonAPIScraper(amazon_config)
        
        # Test search
        query = "PlayStation 5"
        logger.info(f"Testing Amazon API search for: {query}")
        
        # Perform search
        result = scraper.search(query)
        
        if result:
            logger.info("Search successful!")
            logger.info(f"Found product: {result}")
        else:
            logger.error("No results found")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")

if __name__ == "__main__":
    test_amazon_api_scraper() 