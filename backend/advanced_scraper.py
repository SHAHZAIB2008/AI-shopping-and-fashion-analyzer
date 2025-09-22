"""
Advanced Web Scraper for Pakistani Fashion Brands
Features:
- Multiple selector fallbacks
- Rate limiting and respectful scraping
- Image validation and processing
- Price standardization
- Error handling and retries
- Concurrent scraping with limits
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, parse_qs
import re
from typing import List, Dict, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
from PIL import Image
import io

from scraping_config import (
    ENHANCED_BRAND_CONFIG, FALLBACK_SELECTORS, COMMON_PATTERNS,
    CATEGORY_SEARCH_TERMS, PRICE_RANGES, ROTATING_HEADERS, RATE_LIMITS
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedProduct:
    name: str
    brand: str
    price: str
    price_numeric: Optional[float]
    image_url: str
    product_url: str
    description: str
    category: Optional[str] = None
    availability: str = "Available"
    rating: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "image": self.image_url,
            "image_url": self.image_url,
            "link": self.product_url,
            "description": self.description,
            "category": self.category,
            "availability": self.availability,
            "rating": self.rating,
            "price_numeric": self.price_numeric
        }

class AdvancedFashionScraper:
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = time.time()
        self.failed_requests = {}
        
    def get_rotating_headers(self) -> Dict[str, str]:
        """Get rotating headers to avoid detection"""
        return random.choice(ROTATING_HEADERS)
    
    def enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < RATE_LIMITS["delay_between_requests"]:
            sleep_time = RATE_LIMITS["delay_between_requests"] - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Make a request with retries and error handling"""
        for attempt in range(max_retries):
            try:
                self.enforce_rate_limit()
                
                response = self.session.get(
                    url, 
                    headers=self.get_rotating_headers(),
                    timeout=RATE_LIMITS["timeout"],
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Check if response is HTML
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type:
                    logger.warning(f"Non-HTML response from {url}: {content_type}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    self.failed_requests[url] = str(e)
        
        return None
    
    def validate_image_url(self, image_url: str) -> bool:
        """Validate if image URL is accessible and is actually an image"""
        try:
            if not image_url or len(image_url) < 10:
                return False
            
            # Check if URL has image extension
            if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                return False
            
            # Quick HEAD request to check if image is accessible
            response = requests.head(image_url, timeout=5, headers=self.get_rotating_headers())
            content_type = response.headers.get('content-type', '')
            
            return response.status_code == 200 and 'image' in content_type
            
        except Exception as e:
            logger.debug(f"Image validation failed for {image_url}: {e}")
            return False
    
    def extract_price_numeric(self, price_text: str) -> Optional[float]:
        """Extract numeric price value for sorting and filtering"""
        try:
            # Remove common currency symbols and text
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace(',', '')
            
            # Find the first number that looks like a price
            price_match = re.search(r'(\d+\.?\d*)', price_clean)
            if price_match:
                return float(price_match.group(1))
        except Exception as e:
            logger.debug(f"Price extraction failed for '{price_text}': {e}")
        
        return None
    
    def standardize_price(self, price_text: str) -> str:
        """Standardize price format"""
        if not price_text:
            return "Price on request"
        
        # Extract numeric value
        numeric_price = self.extract_price_numeric(price_text)
        if numeric_price:
            # Format with PKR prefix
            return f"PKR {numeric_price:,.0f}"
        
        return price_text.strip()
    
    def clean_product_name(self, name: str) -> str:
        """Clean and standardize product names"""
        if not name:
            return "Fashion Item"
        
        # Remove excessive whitespace
        name = ' '.join(name.split())
        
        # Remove brand name if it's at the beginning (to avoid duplication)
        # This is brand-specific logic
        name = re.sub(r'^(Nishat|Khaadi|Gul Ahmed|Sana Safinaz|Maria B|Alkaram|Cross Stitch|Sapphire)\s*[-:]?\s*', '', name, flags=re.IGNORECASE)
        
        # Limit length
        if len(name) > 80:
            name = name[:80] + "..."
        
        return name.strip().title()
    
    def try_selectors(self, container, selectors_list: List[Dict], element_type: str):
        """Try multiple selectors until one works"""
        for selectors in selectors_list:
            if element_type in selectors:
                element = container.select_one(selectors[element_type])
                if element:
                    return element
        
        # Try fallback selectors
        if element_type in FALLBACK_SELECTORS:
            for fallback_selector in FALLBACK_SELECTORS[element_type]:
                element = container.select_one(fallback_selector)
                if element:
                    return element
        
        return None
    
    def extract_product_from_container(self, container, brand_config: Dict, brand_name: str) -> Optional[ScrapedProduct]:
        """Extract product information from a container using multiple selector strategies"""
        try:
            selectors_list = brand_config["selectors"]
            base_url = brand_config["url"]
            
            # Try to extract image
            img_element = self.try_selectors(container, selectors_list, "image")
            if not img_element:
                return None
            
            image_url = (img_element.get('src') or 
                        img_element.get('data-src') or 
                        img_element.get('data-lazy-src'))
            
            if not image_url:
                return None
            
            # Convert relative URLs to absolute
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = urljoin(base_url, image_url)
            
            # Validate image URL
            if not self.validate_image_url(image_url):
                logger.debug(f"Invalid image URL: {image_url}")
                return None
            
            # Extract title
            title_element = self.try_selectors(container, selectors_list, "title")
            title = title_element.get_text().strip() if title_element else "Fashion Item"
            title = self.clean_product_name(title)
            
            # Extract price
            price_element = self.try_selectors(container, selectors_list, "price")
            price_text = price_element.get_text().strip() if price_element else "Price on request"
            price_standardized = self.standardize_price(price_text)
            price_numeric = self.extract_price_numeric(price_text)
            
            # Extract product link
            link_element = self.try_selectors(container, selectors_list, "link")
            product_url = link_element.get('href') if link_element else '#'
            if product_url.startswith('/'):
                product_url = urljoin(base_url, product_url)
            
            # Create product object
            product = ScrapedProduct(
                name=title,
                brand=brand_name,
                price=price_standardized,
                price_numeric=price_numeric,
                image_url=image_url,
                product_url=product_url,
                description=f"{title} from {brand_name}"
            )
            
            return product
            
        except Exception as e:
            logger.warning(f"Error extracting product from {brand_name}: {e}")
            return None
    
    def scrape_brand_products(self, brand_name: str, search_terms: List[str], max_products: int = 6) -> List[ScrapedProduct]:
        """Scrape products from a specific brand for given search terms"""
        if brand_name not in ENHANCED_BRAND_CONFIG:
            logger.error(f"Brand {brand_name} not found in configuration")
            return []
        
        brand_config = ENHANCED_BRAND_CONFIG[brand_name]
        all_products = []
        
        for search_term in search_terms:
            try:
                # Build search URL
                search_url = brand_config["search_url"]
                search_params = brand_config.get("search_params", {})
                
                # Add search term to params
                if search_params:
                    # Find the parameter for search term
                    for key, value in search_params.items():
                        if value == "":  # Empty value indicates this is the search parameter
                            search_params[key] = search_term
                            break
                    
                    # Build URL with parameters
                    param_string = '&'.join([f"{k}={v}" for k, v in search_params.items()])
                    full_url = f"{search_url}?{param_string}"
                else:
                    full_url = f"{search_url}{search_term}"
                
                logger.info(f"Scraping {brand_name} for '{search_term}': {full_url}")
                
                # Make request
                soup = self.make_request(full_url)
                if not soup:
                    continue
                
                # Extract products using multiple selector strategies
                products = []
                selectors_list = brand_config["selectors"]
                
                for selectors in selectors_list:
                    containers = soup.select(selectors["product_container"])
                    
                    for container in containers[:max_products]:
                        product = self.extract_product_from_container(container, brand_config, brand_name)
                        if product:
                            products.append(product)
                    
                    if products:  # If we found products with this selector, use them
                        break
                
                all_products.extend(products)
                
                # Limit total products per brand
                if len(all_products) >= max_products:
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping {brand_name} for '{search_term}': {e}")
                continue
        
        # Remove duplicates based on product URL
        unique_products = []
        seen_urls = set()
        
        for product in all_products:
            if product.product_url not in seen_urls:
                seen_urls.add(product.product_url)
                unique_products.append(product)
        
        logger.info(f"Successfully scraped {len(unique_products)} unique products from {brand_name}")
        return unique_products[:max_products]
    
    async def scrape_multiple_brands_async(self, search_terms: List[str], max_products_per_brand: int = 3, max_total_products: int = 15) -> List[Dict]:
        """Scrape multiple brands asynchronously"""
        # Prioritize brands that are more likely to work
        priority_brands = ["Nishat Linen", "Khaadi", "Gul Ahmed", "Alkaram Studio", "Sapphire"]
        
        # Create tasks for concurrent execution
        with ThreadPoolExecutor(max_workers=RATE_LIMITS["max_concurrent_requests"]) as executor:
            future_to_brand = {
                executor.submit(
                    self.scrape_brand_products, 
                    brand_name, 
                    search_terms[:2],  # Limit search terms for performance
                    max_products_per_brand
                ): brand_name 
                for brand_name in priority_brands
            }
            
            all_products = []
            completed_count = 0
            
            for future in as_completed(future_to_brand, timeout=30):
                brand_name = future_to_brand[future]
                try:
                    products = future.result(timeout=10)
                    all_products.extend([product.to_dict() for product in products])
                    completed_count += 1
                    logger.info(f"Completed scraping {brand_name} ({completed_count}/{len(priority_brands)})")
                    
                    # Early exit if we have enough products
                    if len(all_products) >= max_total_products:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error scraping {brand_name}: {e}")
        
        # Sort products by price (if available) and remove duplicates
        unique_products = []
        seen_names = set()
        
        for product in all_products:
            product_key = f"{product.get('name', '')}-{product.get('brand', '')}"
            if product_key not in seen_names:
                seen_names.add(product_key)
                unique_products.append(product)
        
        # Sort by price (ascending)
        unique_products.sort(key=lambda x: x.get('price_numeric') or float('inf'))
        
        return unique_products[:max_total_products]
    
    def get_scraping_stats(self) -> Dict:
        """Get scraping statistics"""
        return {
            "total_requests": self.request_count,
            "failed_requests": len(self.failed_requests),
            "success_rate": (self.request_count - len(self.failed_requests)) / max(self.request_count, 1),
            "failed_urls": list(self.failed_requests.keys())
        }

# Global scraper instance
fashion_scraper = AdvancedFashionScraper()

# Utility functions for easy integration

def search_products_by_category(category: str, max_products: int = 12) -> List[Dict]:
    """Search for products by category using predefined search terms"""
    if category in CATEGORY_SEARCH_TERMS:
        search_terms = CATEGORY_SEARCH_TERMS[category][:3]  # Use top 3 terms
        return asyncio.run(fashion_scraper.scrape_multiple_brands_async(search_terms, max_products_per_brand=2, max_total_products=max_products))
    return []

def search_products_by_terms(search_terms: List[str], max_products: int = 12) -> List[Dict]:
    """Search for products using custom search terms"""
    return asyncio.run(fashion_scraper.scrape_multiple_brands_async(search_terms, max_products_per_brand=2, max_total_products=max_products))

def search_single_brand(brand_name: str, search_terms: List[str], max_products: int = 6) -> List[Dict]:
    """Search products from a single brand"""
    products = fashion_scraper.scrape_brand_products(brand_name, search_terms, max_products)
    return [product.to_dict() for product in products]

def filter_products_by_price(products: List[Dict], price_range: str) -> List[Dict]:
    """Filter products by price range"""
    if price_range not in PRICE_RANGES:
        return products
    
    price_config = PRICE_RANGES[price_range]
    min_price = price_config["min"]
    max_price = price_config["max"]
    
    filtered = []
    for product in products:
        price_numeric = product.get('price_numeric')
        if price_numeric and min_price <= price_numeric <= max_price:
            filtered.append(product)
    
    return filtered