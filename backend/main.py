
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
import ollama
import re
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Allow CORS (so frontend can talk to backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Enhanced Pakistani Fashion Brands Configuration with scraping selectors
FASHION_BRANDS = {
    "Khaadi": {
        "url": "https://pk.khaadi.com",
        "json_search_url": "https://pk.khaadi.com/search/suggest.json?q=",
        "description": "Contemporary Pakistani fashion brand"
    },
    "Nishat Linen": {
        "url": "https://nishatlinen.com",
        "json_search_url": "https://nishatlinen.com/search/suggest.json?q=",
        "description": "Premium Pakistani fashion and home textiles"
    },
    "Sapphire": {
        "url": "https://pk.sapphireonline.pk",
        "json_search_url": "https://pk.sapphireonline.pk/search/suggest.json?q=",
        "description": "Modern Pakistani fashion brand"
    },
    "Cross Stitch": {
        "url": "https://www.crossstitch.pk",
        "json_search_url": "https://www.crossstitch.pk/search/suggest.json?q=",
        "description": "Contemporary Pakistani fashion"
    },
    "Gul Ahmed": {
        "url": "https://www.gulahmedshop.com",
        "json_search_url": "https://www.gulahmedshop.com/advancesearch?search=",
        "description": "Contemporary Pakistani fashion"
    },
    "Sana Safinaz": {
        "url": "https://www.sanasafinaz.com",
        "json_search_url": "https://sanasafinaz.com/search?q=",
        "description": "Contemporary Pakistani fashion"
    },
    "Maria B": {
        "url": "https://www.mariab.pk",
        "json_search_url": "https://www.mariab.pk/search?type=product%2Carticle%2Cpage%2Ccollection&options[prefix]=last&q=",
        "description": "Contemporary Pakistani fashion"
    },
        "Alkaram Studio": {
        "url": "https://www.alkaramstudio.com",
        "json_search_url": "https://www.alkaramstudio.com/search?q=",
        "description": "Contemporary Pakistani fashion"
    },
    # , Sana Safinaz, M,  → not Shopify,
    # so we keep them with HTML scraping for now
}

# User agents to rotate for scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.executor = ThreadPoolExecutor(max_workers=5)

    def get_random_headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def scrape_brand_products(self, brand_name: str, search_term: str, max_products: int = 6) -> List[Dict]:
        if brand_name not in FASHION_BRANDS:
            return []
        brand_config = FASHION_BRANDS[brand_name]
        products = []
        try:
            if "json_search_url" in brand_config:
                search_url = f"{brand_config['json_search_url']}{quote(search_term)}"
                resp = self.session.get(search_url, headers=self.get_random_headers(), timeout=10)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("resources", {}).get("results", {}).get("products", [])
                for item in items[:max_products]:
                    name = item.get("title", "Unknown")
                    price = item.get("price", "Price on request")
                    link = item.get("url", "#")
                    # --- Robust image extraction ---
                    image_url = None

                    # Try featured_image
                    fi = item.get("featured_image")
                    if isinstance(fi, dict):
                        image_url = fi.get("url")

                    # Try image field (string or dict)
                    if not image_url and "image" in item:
                        if isinstance(item["image"], str):
                            image_url = item["image"]
                        elif isinstance(item["image"], dict):
                            image_url = item["image"].get("src") or item["image"].get("url")

                    # Try variants
                    if not image_url and "variants" in item:
                        for var in item["variants"]:
                            fi = var.get("featured_image") or {}
                            if "url" in fi:
                                image_url = fi["url"]
                                break

                    # Normalize URL
                    if image_url:
                        if image_url.startswith("//"):
                            image_url = "https:" + image_url
                        elif image_url.startswith("/"):
                            image_url = brand_config["url"].rstrip("/") + image_url

                    products.append({
                        "name": name,
                        "brand": brand_name,
                        "price": price,
                        "image": image_url,
                        "link": brand_config["url"] + link,
                        "description": f"Fashion item from {brand_name}"
                    })
                return products
            else:
                return self.scrape_brand_products_html(brand_name, search_term, max_products)
        except Exception as e:
            logger.error(f"Error scraping {brand_name}: {e}")
            return []

    def extract_product_info(self, container, selectors: Dict, brand_name: str, base_url: str) -> Optional[Dict]:
        """Extract product information from a container element"""
        try:
            # Extract image
            img_element = container.select_one(selectors['image'])
            if not img_element:
                return None
            
            image_url = img_element.get('src') or img_element.get('data-src')
            if image_url:
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = urljoin(base_url, image_url)
            
            # Extract title
            title_element = container.select_one(selectors['title'])
            title = title_element.get_text().strip() if title_element else "Product"
            
            # Extract price
            price_element = container.select_one(selectors['price'])
            price = price_element.get_text().strip() if price_element else "Price on request"
            
            # Extract product link
            link_element = container.select_one(selectors['link'])
            product_link = link_element.get('href') if link_element else '#'
            if product_link.startswith('/'):
                product_link = urljoin(base_url, product_link)
            
            # Clean and format the data
            return {
                "name": self.clean_text(title)[:100],  # Limit title length
                "brand": brand_name,
                "price": self.clean_price(price),
                "image": image_url,
                "image_url": image_url,  # Keep both for compatibility
                "link": product_link,
                "description": f"Fashion item from {brand_name}"
            }
        
        except Exception as e:
            logger.warning(f"Error extracting product info: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and format text"""
        if not text:
            return ""
        return ' '.join(text.split())
    
    def clean_price(self, price: str) -> str:
        """Clean and format price"""
        if not price:
            return "Price on request"
        
        # Remove extra whitespace
        price = ' '.join(price.split())
        
        # If price doesn't contain PKR or Rs, assume it's in PKR
        if not any(curr in price.upper() for curr in ['PKR', 'RS', '₨']):
            # Extract numbers and add PKR prefix
            numbers = re.findall(r'[\d,]+', price)
            if numbers:
                return f"PKR {numbers[0]}"
        
        return price
    
    async def scrape_multiple_brands_async(self, search_terms: List[str], max_products_per_brand: int = 3) -> List[Dict]:
        """Scrape multiple brands asynchronously for given search terms"""
        all_products = []
        
        # Select top brands for faster results
        priority_brands = ["Khaadi", "Nishat Linen", "Gul Ahmed", "Alkaram Studio","Sapphire", "Cross Stitch","Maria B","Sana Safinaz"]
        
        tasks = []
        for brand_name in priority_brands:
            for search_term in search_terms[:2]:  # Limit search terms for performance
                task = asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    self.scrape_brand_products, 
                    brand_name, 
                    search_term, 
                    max_products_per_brand
                )
                tasks.append(task)
        
        # Wait for all scraping tasks to complete with timeout
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=30)
            
            for result in results:
                if isinstance(result, list):
                    all_products.extend(result)
        
        except asyncio.TimeoutError:
            logger.warning("Scraping timeout - returning partial results")
        
        # Remove duplicates and limit results
        seen_links = set()
        unique_products = []
        
        for product in all_products:
            if product.get('link') not in seen_links:
                seen_links.add(product.get('link'))
                unique_products.append(product)
                
                if len(unique_products) >= 12:  # Limit total products
                    break
        
        return unique_products

# Initialize global scraper
scraper = WebScraper()

# Fashion keywords that trigger shopping links
FASHION_KEYWORDS = [
    'kurti', 'kurta', 'shirt', 'dress', 'dupatta', 'shalwar', 'kameez', 
    'lawn', 'chiffon', 'silk', 'cotton', 'linen', 'blouse', 'top',
    'pants', 'trouser', 'jeans', 'skirt', 'scarf', 'shawl', 'jacket',
    'coat', 'sweater', 'cardigan', 'lehenga', 'gharara', 'sharara',
    'saree', 'abaya', 'hijab', 'formal wear', 'casual wear', 'ethnic wear'
]

def extract_fashion_items(text):
    """Extract fashion-related items from the analysis text"""
    fashion_items = []
    text_lower = text.lower()
    
    for keyword in FASHION_KEYWORDS:
        if keyword in text_lower:
            fashion_items.append(keyword)
    
    # Extract color + clothing combinations
    color_pattern = r'\b(blue|red|green|yellow|black|white|pink|purple|orange|brown|grey|gray|navy|maroon|beige|cream|gold|silver)\s+(kurti|kurta|shirt|dress|dupatta|shalwar|kameez|lawn|blouse|top|pants|trouser|skirt|scarf|shawl|jacket|coat|sweater|cardigan|lehenga|gharara|sharara|saree|abaya)\b'
    color_matches = re.findall(color_pattern, text_lower)
    
    for color, item in color_matches:
        fashion_items.append(f"{color} {item}")
    
    return list(set(fashion_items))

def generate_search_terms(question: str, fashion_items: List[str]) -> List[str]:
    """Generate search terms based on question and detected fashion items"""
    search_terms = []
    
    # Add detected fashion items
    search_terms.extend(fashion_items[:3])  # Limit to top 3 items
    
    # Add category-based terms
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['wedding', 'bridal', 'bride', 'marriage', 'nikah', 'walima']):
        search_terms.extend(['bridal', 'wedding dress', 'lehenga'])
    elif any(word in question_lower for word in ['party', 'function', 'event', 'celebration']):
        search_terms.extend(['party wear', 'fancy dress'])
    elif any(word in question_lower for word in ['casual', 'daily', 'everyday']):
        search_terms.extend(['kurti', 'casual shirt'])
    elif any(word in question_lower for word in ['formal', 'office', 'work']):
        search_terms.extend(['formal wear', 'office shirt'])
    
    # Remove duplicates and empty terms
    search_terms = [term.strip() for term in search_terms if term.strip()]
    return list(set(search_terms))

@app.post("/analyze_image/")
async def analyze_image(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            return JSONResponse({
                "status": "error",
                "message": "Please upload a valid image file"
            }, status_code=400)
        
        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{file_ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Analyze image with Ollama vision model
        analysis_prompt = """Analyze this image comprehensively. Describe:

6. If clothing/fashion items are visible, describe them in detail including:
   - Type of garment (kurti, shirt, dress, dupatta, etc.)
   - Colors and patterns
   - Style and cut
   - Fabric type if identifiable
   - Any fashion-related accessories

Be detailed and thorough as this analysis will be used to answer follow-up questions. Pay special attention to any Pakistani or South Asian fashion elements."""

        # Send image to Ollama vision model
        response = ollama.chat(
            model="llama3.2-vision",
            messages=[{
                "role": "user",
                "content": analysis_prompt,
                "images": [file_path]
            }],
            options={
                "num_gpu": 25, 
                "num_thread": 4,
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        )

        image_analysis = response["message"]["content"]
        fashion_items = extract_fashion_items(image_analysis)
        
        # Clean up uploaded file
        os.remove(file_path)

        return JSONResponse({
            "status": "success",
            "image_analysis": image_analysis,
            "fashion_items": fashion_items,
            "message": "Image analyzed successfully. You can now ask questions about it."
        })

    except FileNotFoundError:
        return JSONResponse({
            "status": "error",
            "message": "Ollama model 'llama3.2-vision' not found. Please run: ollama pull llama3.2-vision"
        }, status_code=500)
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        return JSONResponse({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status_code=500)

def detect_query_category(question):
    """Detect what type of clothing the user is asking for"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['wedding', 'bridal', 'bride', 'marriage', 'nikah', 'walima']):
        return 'wedding'
    elif any(word in question_lower for word in ['party', 'function', 'event', 'celebration', 'engagement']):
        return 'party'
    elif any(word in question_lower for word in ['casual', 'daily', 'everyday', 'comfort', 'home']):
        return 'casual'
    elif any(word in question_lower for word in ['formal', 'office', 'work', 'professional', 'business']):
        return 'formal'
    else:
        return 'casual'

@app.post("/ask_question/")
async def ask_question(file: UploadFile = File(...), question: str = Form(...), image_analysis: str = Form(...)):
    try:
        # Save uploaded file for question answering
        file_ext = os.path.splitext(file.filename)[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{file_ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate AI answer using Ollama
        question_prompt = f"""Based on this image and the following comprehensive analysis:

PREVIOUS ANALYSIS:
{image_analysis}

Now answer this specific question about the image: {question}

Provide a focused, direct answer based on what you can see in the image and the analysis above.

If the user is asking for clothing recommendations (like wedding dress, party wear, etc.), acknowledge their request and mention that you will provide specific product suggestions with images and prices from Pakistani fashion brands."""

        response = ollama.chat(
            model="llama3.2-vision",
            messages=[{
                "role": "user",
                "content": question_prompt,
                "images": [file_path]
            }],
            options={
                "num_gpu": 25,
                "num_thread": 4,
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        )

        base_answer = response["message"]["content"]
        
        # Check if user is asking for product recommendations
        shopping_keywords = ['give me', 'show me', 'find', 'buy', 'purchase', 'shop', 'want', 'need', 'looking for']
        is_shopping_query = any(keyword in question.lower() for keyword in shopping_keywords)
        
        products = []
        query_category = detect_query_category(question)
        
        if is_shopping_query:
            # Extract fashion items from the analysis and question
            fashion_items = extract_fashion_items(image_analysis + " " + question)
            search_terms = generate_search_terms(question, fashion_items)
            
            if search_terms:
                logger.info(f"Scraping products for terms: {search_terms}")
                base_answer += "\n\n🛍️ **SEARCHING LIVE PRODUCTS...**\n"
                base_answer += "Finding the latest products from Pakistani fashion brands...\n"
                
                # Scrape live products from websites
                try:
                    new_products = await scraper.scrape_multiple_brands_async(search_terms, max_products_per_brand=2)

                    if new_products:
                        base_answer += f"\n✅ Found {len(new_products)} fresh products from top Pakistani brands!"
                        base_answer += "\n\nHere are the latest options with real images and current prices:"
                        products = new_products  # <-- ADD THIS LINE

                except Exception as e:
                    logger.error(f"Error during product scraping: {e}")
                    base_answer += f"\n⚠️ There was an issue fetching live products: {str(e)}"
        
        # Clean up uploaded file
        os.remove(file_path)

        return JSONResponse({
            "status": "success",
            "answer": base_answer,
            "question": question,
            "products": products,
            "category": query_category if is_shopping_query else None,
            "total_products_found": len(products)
        })

    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        return JSONResponse({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status_code=500)

@app.get("/brands/")
async def get_brands():
    """Get all available fashion brands"""
    return JSONResponse({
        "brands": FASHION_BRANDS,
        "total_brands": len(FASHION_BRANDS),
        "scraping_enabled": True
    })

@app.post("/test_scraping/")
async def test_scraping(search_term: str = Form(...), brand_name: str = Form(None)):
    """Test scraping functionality for debugging"""
    try:
        if brand_name and brand_name in FASHION_BRANDS:
            products = scraper.scrape_brand_products(brand_name, search_term, max_products=5)
        else:
            products = await scraper.scrape_multiple_brands_async([search_term], max_products_per_brand=3)
        
        return JSONResponse({
            "status": "success",
            "search_term": search_term,
            "brand_name": brand_name,
            "products_found": len(products),
            "products": products
        })
    
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Error during scraping test: {str(e)}"
        }, status_code=500)

@app.get("/gpu_status/")
async def gpu_status():
    try:
        models = ollama.list()
        
        import subprocess
        try:
            gpu_info = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader,nounits'], text=True)
            gpu_available = True
        except:
            gpu_info = "GPU not available or nvidia-smi not found"
            gpu_available = False
            
        return JSONResponse({
            "gpu_available": gpu_available,
            "gpu_info": gpu_info,
            "loaded_models": [model["name"] for model in models.get("models", [])],
            "scraping_status": "enabled",
            "supported_brands": list(FASHION_BRANDS.keys())
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@app.get("/")
async def root():
    return {
        "message": "AI Fashion Analyzer with Live Product Scraping is running!", 
        "gpu_optimized": "RTX 3050",
        "features": [
            "Image Analysis with Ollama Vision",
            "Live Product Scraping",
            "Real-time Brand Website Integration", 
            "Pakistani Fashion Brands",
            "Product Images & Prices",
            "Smart Search Term Generation"
        ],
        "total_brands": len(FASHION_BRANDS),
        "scraping_enabled": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
