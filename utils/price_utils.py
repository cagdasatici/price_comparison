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
        'console': {
            'ps5': (350, 800),  # PS5 specific range
            'xbox': (350, 800),  # Xbox specific range
            'switch': (250, 500),  # Nintendo Switch specific range
            'default': (100, 1000)  # Default console range
        },
        'game': (10, 100),       # Video games
        'accessory': (5, 200)    # Gaming accessories
    }
    
    # Determine product type based on keywords
    product_lower = product.lower()
    
    # Check for specific console types
    if 'ps5' in product_lower or 'playstation 5' in product_lower:
        min_price, max_price = price_ranges['console']['ps5']
    elif 'xbox' in product_lower:
        min_price, max_price = price_ranges['console']['xbox']
    elif 'switch' in product_lower or 'nintendo' in product_lower:
        min_price, max_price = price_ranges['console']['switch']
    elif any(keyword in product_lower for keyword in ['console', 'playstation', 'nintendo']):
        min_price, max_price = price_ranges['console']['default']
    elif any(keyword in product_lower for keyword in ['game', 'spel', 'software']):
        min_price, max_price = price_ranges['game']
    else:
        min_price, max_price = price_ranges['accessory']
    
    # Check if price is within the valid range for the product type
    return min_price <= price <= max_price 