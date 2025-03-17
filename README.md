# Price Comparison Tool

A Python application for comparing prices across multiple Dutch e-commerce websites. This tool helps you find the best deals on gaming consoles, games, and accessories.

## Features

- Real-time price comparison across multiple stores
- Modern UI with dark mode support
- Progress tracking for each store search
- Price validation to ensure reasonable results
- Support for multiple product categories (consoles, games, accessories)
- Direct links to product pages

## Installation

1. Make sure you have Python 3.8 or higher installed
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/price_comparison.git
   cd price_comparison
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Enter the product name in the search box
3. Click "Search" to start the price comparison
4. View results in the table below
5. Click on any result to open the product page in your browser

## Supported Stores

- Bol.com
- Amazon.nl
- Coolblue.nl
- MediaMarkt.nl
- Tweakers.net
- Wehkamp.nl
- BCC.nl
- Alternate.nl
- Azerty.nl
- GameMania.nl
- Bart Smit
- Intertoys
- And more...

## Project Structure

```
price_comparison/
├── main.py              # Main entry point
├── ui/
│   └── app.py          # UI components and main application class
├── scrapers/
│   └── store_scrapers.py  # Store-specific scraping functions
├── utils/
│   └── price_utils.py  # Helper functions for price handling
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 