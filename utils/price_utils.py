from difflib import SequenceMatcher
import re

def string_similarity(a, b):
    """Calculate the similarity between two strings using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_price(price_str):
    """Extract numeric price from string, handling various formats."""
    try:
        # Remove currency symbols and other non-numeric characters except decimal point
        price_str = re.sub(r'[^\d.]', '', price_str)
        
        # Handle empty or invalid strings
        if not price_str:
            return None
            
        # Convert to float
        price = float(price_str)
        return price
    except (ValueError, TypeError):
        return None

def validate_price(price, product):
    """Validate if a price is within reasonable ranges for different product types."""
    if price is None:
        return False
        
    # Define price ranges for different product types
    price_ranges = {
        'console': (100, 1000),  # Gaming consoles
        'game': (10, 100),       # Video games
        'accessory': (5, 200)    # Gaming accessories
    }
    
    # Determine product type based on keywords
    product_lower = product.lower()
    
    if any(keyword in product_lower for keyword in ['ps5', 'xbox', 'switch', 'console', 'playstation', 'nintendo']):
        product_type = 'console'
    elif any(keyword in product_lower for keyword in ['game', 'spel', 'software']):
        product_type = 'game'
    else:
        product_type = 'accessory'
    
    # Check if price is within the valid range for the product type
    min_price, max_price = price_ranges[product_type]
    return min_price <= price <= max_price 