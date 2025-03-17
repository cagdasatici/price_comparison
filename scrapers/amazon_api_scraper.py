import logging
from typing import Dict, List, Optional, Any
from amazon.api import AmazonAPI
from config.stores import STORE_CONFIGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonAPIScraper:
    def __init__(self, store_config):
        """
        Initialize Amazon API scraper.
        
        Args:
            store_config: Store configuration
        """
        self.store_config = store_config
        
        # Get API credentials from environment variables
        self.access_key = store_config.custom_headers.get('AWS_ACCESS_KEY')
        self.secret_key = store_config.custom_headers.get('AWS_SECRET_KEY')
        self.associate_tag = store_config.custom_headers.get('ASSOCIATE_TAG')
        
        if not all([self.access_key, self.secret_key, self.associate_tag]):
            raise ValueError("Missing required Amazon API credentials")
        
        # Initialize Amazon API client
        self.amazon = AmazonAPI(
            self.access_key,
            self.secret_key,
            self.associate_tag,
            region='NL'  # Netherlands region
        )

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for products using Amazon Product Advertising API.
        """
        try:
            logger.info(f"Searching Amazon for: {query}")
            
            # Search for products
            products = self.amazon.search(
                Keywords=query,
                SearchIndex='All',
                ResponseGroup='ItemAttributes,Offers'
            )
            
            # Get the first product
            product = next(products, None)
            if not product:
                logger.warning("No products found")
                return None
            
            # Extract product information
            try:
                # Get price
                price = None
                if hasattr(product, 'price_and_currency'):
                    price = product.price_and_currency[0]
                elif hasattr(product, 'offer_url'):
                    # Try to get price from offer URL
                    price = product.offer_url.split('price=')[-1].split('&')[0]
                
                if not price:
                    logger.warning("No price found")
                    return None
                
                # Format price
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price format: {price}")
                    return None
                
                result = {
                    'title': product.title,
                    'price': f"{price:.2f}",
                    'link': product.offer_url,
                    'description': product.get('EditorialReview', {}).get('Content', ''),
                    'store': self.store_config.name
                }
                
                logger.info(f"Found product: {result}")
                return result
                
            except Exception as e:
                logger.error(f"Error extracting product information: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return None 