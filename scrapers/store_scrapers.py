import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from utils.price_utils import extract_price, validate_price, string_similarity
import random
import time

class StoreScrapers:
    def __init__(self):
        self.stores = [
            'Bol.com', 'Amazon.nl', 'Coolblue.nl', 'MediaMarkt.nl', 'Tweakers.net',
            'Wehkamp.nl', 'BCC.nl', 'Alternate.nl', 'Azerty.nl', 'GameMania.nl',
            'Bart Smit', 'Intertoys', 'Playsi.nl', '4Launch.nl', 'Centralpoint.nl',
            'Videoland.nl', 'Nedgame.nl', 'Game Mania', 'GameStop.nl',
            'Dreamland.nl', 'Toys XL', 'ToyChamp', 'Beslist.nl'
        ]

    def get_store_list(self):
        return self.stores

    def get_search_functions(self):
        return {
            'Bol.com': self.search_bol,
            'Amazon.nl': self.search_amazon,
            'Coolblue.nl': self.search_coolblue,
            'MediaMarkt.nl': self.search_mediamarkt,
            'Tweakers.net': self.search_tweakers,
            'Wehkamp.nl': self.search_wehkamp,
            'BCC.nl': self.search_bcc,
            'Alternate.nl': self.search_alternate,
            'Azerty.nl': self.search_azerty,
            'GameMania.nl': self.search_gamemania,
            'Bart Smit': self.search_bart_smit,
            'Intertoys': self.search_intertoys,
            'Playsi.nl': self.search_playsi,
            '4Launch.nl': self.search_4launch,
            'Centralpoint.nl': self.search_centralpoint,
            'Videoland.nl': self.search_videoland,
            'Nedgame.nl': self.search_nedgame,
            'Game Mania': self.search_gamemania,
            'GameStop.nl': self.search_gamestop,
            'Dreamland.nl': self.search_dreamland,
            'Toys XL': self.search_toys_xl,
            'ToyChamp': self.search_toychamp,
            'Beslist.nl': self.search_beslist
        }

    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    def make_request(self, url, headers=None, verify=True):
        try:
            if headers is None:
                headers = self.get_headers()
            response = requests.get(url, headers=headers, verify=verify, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error for {url}: {str(e)}")
            return None

    def get_random_user_agent(self):
        """Get a random User-Agent string to avoid detection."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.92'
        ]
        return random.choice(user_agents)

    def search_bol(self, product):
        try:
            url = f"https://www.bol.com/nl/nl/s/?searchtext={quote(product)}"
            response = self.make_request(url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            for item in soup.find_all('li', class_='product-item--row'):
                title_elem = item.find('a', class_='product-title')
                price_elem = item.find('span', class_='promo-price')
                desc_elem = item.find('p', class_='product-description')
                
                if title_elem and price_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip()
                    description = desc_elem.text.strip() if desc_elem else ""
                    link = title_elem['href'] if title_elem else None
                    if link and not link.startswith('http'):
                        link = 'https://www.bol.com' + link
                    
                    similarity = string_similarity(product, title)
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'description': description,
                        'similarity': similarity,
                        'link': link
                    })
            
            if products:
                products.sort(key=lambda x: x['similarity'], reverse=True)
                best_match = products[0]
                
                price_value = extract_price(best_match['price'])
                if validate_price(price_value, product):
                    return {
                        'store': 'Bol.com',
                        'price': best_match['price'],
                        'title': best_match['title'],
                        'description': best_match['description'],
                        'link': best_match['link']
                    }
                else:
                    for product in products[1:]:
                        price_value = extract_price(product['price'])
                        if validate_price(price_value, product):
                            return {
                                'store': 'Bol.com',
                                'price': product['price'],
                                'title': product['title'],
                                'description': product['description'],
                                'link': product['link']
                            }
            
            return None
        except Exception as e:
            print(f"Bol.com error: {str(e)}")
            return None

    def search_amazon(self, product):
        try:
            # Clean and normalize the search query
            search_query = product.lower().strip()
            url = f"https://www.amazon.nl/s?k={quote(search_query)}"
            
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            # Add random delay between 1-3 seconds
            time.sleep(random.uniform(1, 3))
            
            # First try with regular request
            response = requests.get(url, headers=headers, timeout=10)
            
            # Check for CAPTCHA or other blocking
            if 'captcha' in response.text.lower() or 'robot check' in response.text.lower():
                print("Amazon CAPTCHA detected, trying with session...")
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=10)
            
            # If we get a 503 or other error, try with session
            if response.status_code in [503, 429, 403]:
                print(f"Amazon returned status code {response.status_code}, retrying with session...")
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=10)
            
            if not response or response.status_code != 200:
                print(f"Amazon error: Status code {response.status_code if response else 'None'}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different product containers
            product_containers = [
                soup.find_all('div', class_='s-result-item'),
                soup.find_all('div', class_='s-card-container'),
                soup.find_all('div', {'data-component-type': 's-search-result'}),
                soup.find_all('div', class_='s-result-item s-asin'),
                soup.find_all('div', class_='s-result-item s-asin s-grid-view-item')
            ]
            
            products = []
            for container in product_containers:
                for item in container:
                    # Skip sponsored items
                    if item.find('span', class_='a-color-secondary', string=lambda x: x and 'sponsored' in x.lower()):
                        continue
                    
                    # Try different title selectors
                    title_elem = (
                        item.find('span', class_='a-text-normal') or
                        item.find('h2', class_='a-size-mini') or
                        item.find('h2', class_='a-size-base') or
                        item.find('h2', class_='a-size-medium') or
                        item.find('h2', class_='a-size-large') or
                        item.find('h2', class_='a-size-small') or
                        item.find('h2', class_='a-size-base-plus') or
                        item.find('h2', class_='a-size-medium-plus')
                    )
                    
                    # Try different link selectors
                    link_elem = (
                        item.find('a', class_='a-link-normal') or
                        item.find('a', class_='a-link-normal s-no-outline') or
                        item.find('a', class_='a-link-normal s-underline-text') or
                        item.find('a', class_='a-link-normal s-navigation-item') or
                        item.find('a', class_='a-link-normal s-underline-text s-underline-link-text')
                    )
                    
                    if not title_elem or not link_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = 'https://www.amazon.nl' + link
                    
                    # Try different price selectors
                    price = None
                    price_selectors = [
                        ('span', 'a-price-whole'),
                        ('span', 'a-price'),
                        ('span', 'a-offscreen'),
                        ('span', 'a-color-price'),
                        ('span', 'a-price a-text-price'),
                        ('span', 'a-price a-text-normal'),
                        ('span', 'a-price-nowrap'),
                        ('span', 'a-price a-text-price a-size-base'),
                        ('span', 'a-price a-text-price a-size-medium'),
                        ('span', 'a-price a-text-price a-size-large'),
                        ('span', 'a-price a-text-price a-size-small'),
                        ('span', 'a-price a-text-price a-size-medium a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-base a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-small a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-base a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-small a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-large a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-medium a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-base a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-small a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-base a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-small a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-large a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-medium a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-base a-color-secondary'),
                        ('span', 'a-price a-text-price a-size-small a-color-secondary')
                    ]
                    
                    for tag, class_name in price_selectors:
                        price_elem = item.find(tag, class_=class_name)
                        if price_elem:
                            price = price_elem.text.strip()
                            break
                    
                    # If no price found, try to find the lowest price from multiple sellers
                    if not price:
                        price_elem = item.find('div', class_='a-row a-size-base a-color-secondary')
                        if price_elem:
                            price = price_elem.text.strip()
                    
                    # If still no price, try to find the price in the product details
                    if not price:
                        price_elem = item.find('div', class_='a-section a-spacing-none a-spacing-top-micro')
                        if price_elem:
                            price = price_elem.text.strip()
                    
                    # Clean up price string
                    if price:
                        # Handle "from" prices
                        if 'vanaf' in price.lower() or 'from' in price.lower():
                            price = re.sub(r'vanaf|from', '', price, flags=re.IGNORECASE).strip()
                        
                        # Handle price ranges
                        if '-' in price:
                            price = price.split('-')[0].strip()
                        
                        # Remove currency symbols and clean up the price string
                        price = re.sub(r'[^\d.]', '', price)
                        if price:
                            price = f"€{price}"
                    
                    # Calculate similarity with search query
                    similarity = string_similarity(search_query, title.lower())
                    
                    # Boost similarity based on word matches
                    search_words = set(search_query.split())
                    title_words = set(title.lower().split())
                    word_matches = len(search_words.intersection(title_words))
                    similarity += (word_matches / len(search_words)) * 0.3
                    
                    # Boost similarity for exact matches
                    if search_query in title.lower():
                        similarity += 0.2
                    
                    # Only add products with valid prices
                    if price:
                        products.append({
                            'title': title,
                            'price': price,
                            'similarity': min(1.0, similarity),  # Cap similarity at 1.0
                            'link': link
                        })
            
            # Sort by similarity and find the best match
            if products:
                products.sort(key=lambda x: x['similarity'], reverse=True)
                best_match = products[0]
                
                # Validate price
                price_value = extract_price(best_match['price'])
                if validate_price(price_value, product):
                    return {
                        'store': 'Amazon.nl',
                        'price': best_match['price'],
                        'title': best_match['title'],
                        'description': '',
                        'link': best_match['link']
                    }
                else:
                    # Try next best match if price is invalid
                    for product in products[1:]:
                        price_value = extract_price(product['price'])
                        if validate_price(price_value, product):
                            return {
                                'store': 'Amazon.nl',
                                'price': product['price'],
                                'title': product['title'],
                                'description': '',
                                'link': product['link']
                            }
            
            return None
        except Exception as e:
            print(f"Amazon error: {str(e)}")
            return None

    def search_mediamarkt(self, product):
        try:
            url = f"https://www.mediamarkt.nl/zoeken.html?query={quote(product)}"
            headers = self.get_headers()
            response = self.make_request(url, headers=headers)
            if not response:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            for item in soup.find_all('div', class_='product-wrapper'):
                title_elem = item.find('div', class_='content')
                price_elem = item.find('div', class_='price-box')
                link_elem = item.find('a')
                
                if title_elem and price_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip()
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = 'https://www.mediamarkt.nl' + link
                    
                    similarity = string_similarity(product, title)
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'similarity': similarity,
                        'link': link
                    })
            
            if products:
                products.sort(key=lambda x: x['similarity'], reverse=True)
                best_match = products[0]
                
                price_value = extract_price(best_match['price'])
                if validate_price(price_value, product):
                    return {
                        'store': 'MediaMarkt.nl',
                        'price': best_match['price'],
                        'title': best_match['title'],
                        'description': '',
                        'link': best_match['link']
                    }
                else:
                    for product in products[1:]:
                        price_value = extract_price(product['price'])
                        if validate_price(price_value, product):
                            return {
                                'store': 'MediaMarkt.nl',
                                'price': product['price'],
                                'title': product['title'],
                                'description': '',
                                'link': product['link']
                            }
            
            return None
        except Exception as e:
            print(f"MediaMarkt error: {str(e)}")
            return None

    def search_gamemania(self, product):
        try:
            url = f"https://www.gamemania.nl/zoeken?q={quote(product)}"
            headers = self.get_headers()
            response = self.make_request(url, headers=headers, verify=False)
            if not response:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            for item in soup.find_all('div', class_='product-item'):
                title_elem = item.find('h3', class_='product-title')
                price_elem = item.find('span', class_='price')
                link_elem = item.find('a', class_='product-link')
                
                if title_elem and price_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip()
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = 'https://www.gamemania.nl' + link
                    
                    similarity = string_similarity(product, title)
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'similarity': similarity,
                        'link': link
                    })
            
            if products:
                products.sort(key=lambda x: x['similarity'], reverse=True)
                best_match = products[0]
                
                price_value = extract_price(best_match['price'])
                if validate_price(price_value, product):
                    return {
                        'store': 'Game Mania',
                        'price': best_match['price'],
                        'title': best_match['title'],
                        'description': '',
                        'link': best_match['link']
                    }
                else:
                    for product in products[1:]:
                        price_value = extract_price(product['price'])
                        if validate_price(price_value, product):
                            return {
                                'store': 'Game Mania',
                                'price': product['price'],
                                'title': product['title'],
                                'description': '',
                                'link': product['link']
                            }
            
            return None
        except Exception as e:
            print(f"Game Mania error: {str(e)}")
            return None

    # Add all other store search methods here...
    # (The rest of the store search methods would be added here, following the same pattern) 