import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from utils.price_utils import extract_price, validate_price, string_similarity

class StoreScrapers:
    def __init__(self):
        self.stores = [
            'Bol.com', 'Amazon.nl', 'Coolblue.nl', 'MediaMarkt.nl', 'Tweakers.net',
            'Wehkamp.nl', 'BCC.nl', 'Alternate.nl', 'Azerty.nl', 'GameMania.nl',
            'Bart Smit', 'Intertoys', 'Playsi.nl', '4Launch.nl', 'Centralpoint.nl',
            'Videoland.nl', 'Nedgame.nl', 'Game Mania', 'GameStop.nl',
            'Dreamland.nl', 'Toys XL', 'ToyChamp', 'Beslist.nl', 'Beslist - Bol.com',
            'Beslist - Coolblue', 'Beslist - MediaMarkt', 'Beslist - Wehkamp',
            'Beslist - BCC', 'Beslist - Alternate', 'Beslist - Azerty'
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
            url = f"https://www.amazon.nl/s?k={quote(product)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if not response or response.status_code != 200:
                print(f"Amazon error: Status code {response.status_code if response else 'None'}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            for item in soup.find_all('div', class_='s-result-item'):
                title_elem = item.find('span', class_='a-text-normal')
                link_elem = item.find('a', class_='a-link-normal')
                
                if not title_elem or not link_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = link_elem['href'] if link_elem else None
                if link and not link.startswith('http'):
                    link = 'https://www.amazon.nl' + link
                
                # Look for different price formats
                price = None
                price_elem = None
                
                # Try different price selectors
                price_selectors = [
                    ('span', 'a-price-whole'),
                    ('span', 'a-price'),
                    ('span', 'a-offscreen'),
                    ('span', 'a-color-price'),
                    ('span', 'a-price a-text-price'),
                    ('span', 'a-price a-text-normal'),
                    ('span', 'a-price-nowrap'),
                    ('span', 'a-price a-text-price a-size-base'),
                    ('span', 'a-price a-text-price a-size-medium')
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
                    # Remove currency symbols and clean up the price string
                    price = re.sub(r'[^\d.]', '', price)
                    if price:
                        price = f"€{price}"
                
                # Calculate similarity with search query
                similarity = string_similarity(product, title)
                
                # Only add products with valid prices
                if price:
                    products.append({
                        'title': title,
                        'price': price,
                        'similarity': similarity,
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