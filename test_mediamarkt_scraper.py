import logging
from scrapers.mediamarkt_scraper import MediaMarktScraper
import json
from jinja2 import Template
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_html(query: str, results: list) -> str:
    """Generate HTML page from search results"""
    # Read template
    template_path = os.path.join('templates', 'results.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # Render template with results
    return template.render(query=query, results=results)

def test_mediamarkt_scraper():
    try:
        # Create scraper
        scraper = MediaMarktScraper()
        
        # Test search
        query = "ipad"
        logger.info(f"Testing MediaMarkt search for: {query}")
        
        # Perform search with options
        results = scraper.search(
            query=query,
            max_results=20,
            sort_by='price_low_to_high'  # Sort by price ascending
        )
        
        if results:
            logger.info(f"Search successful! Found {len(results)} products")
            
            # Generate HTML
            html = generate_html(query, results)
            
            # Save HTML
            output_path = 'results.html'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Results saved to {output_path}")
            
            # Print summary
            for i, result in enumerate(results, 1):
                print(f"\nProduct {i}:")
                print(f"Title: {result['title']}")
                print(f"Price: €{result['price']}")
                print(f"Available Online: {'Yes' if result['available_online'] else 'No'}")
                print(f"Link: {result['link']}")
                print("-" * 50)
        else:
            logger.error("No results found")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")

if __name__ == "__main__":
    test_mediamarkt_scraper() 