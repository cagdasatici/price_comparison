# Price Comparison Scraper

A Python-based web scraping tool that collects product information from various Dutch e-commerce websites for price comparison.

## Features

- Scrapes product information from multiple stores:
  - Amazon.nl
  - MediaMarkt.nl
  - HEMA.nl
  - Marktplaats.nl
- Extracts detailed product information including:
  - Title
  - Price
  - Description
  - Image URL
  - Product URL
  - Availability
- Generates HTML reports with search results
- Supports sorting by price and relevance
- Handles pagination and multiple results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/price_comparison.git
cd price_comparison
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

```python
from scrapers.amazon_scraper import AmazonScraper
from scrapers.mediamarkt_scraper import MediaMarktScraper
from scrapers.hema_scraper import HemaScraper

# Initialize scrapers
amazon_scraper = AmazonScraper()
mediamarkt_scraper = MediaMarktScraper()
hema_scraper = HemaScraper()

# Search for products
amazon_results = amazon_scraper.search("PlayStation 5", max_results=5)
mediamarkt_results = mediamarkt_scraper.search("iPad", sort_by="price_low_to_high")
hema_results = hema_scraper.search("finger trainer")

# Results are returned as a list of dictionaries containing product information
```

## Project Structure

```
price_comparison/
├── scrapers/
│   ├── __init__.py
│   ├── amazon_scraper.py
│   ├── mediamarkt_scraper.py
│   ├── hema_scraper.py
│   └── marktplaats_scraper.py
├── templates/
│   └── results.html
├── test_amazon_scraper.py
├── test_mediamarkt_scraper.py
├── test_hema_scraper.py
├── requirements.txt
└── README.md
```

## Dependencies

- Python 3.8+
- Selenium
- BeautifulSoup4
- Requests
- Jinja2

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 