"""
Scraping Configuration for Pakistani Fashion Brands
This file contains the detailed scraping configuration for each brand's website.
You can easily update selectors here when websites change their structure.
"""

# Alternative selectors for different page layouts
FALLBACK_SELECTORS = {
    "image": [
        "img[src*='product']",
        "img[alt*='product']",
        ".product img",
        ".item img",
        "img[data-src]"
    ],
    "title": [
        ".product-title",
        ".product-name",
        ".item-title",
        "h3",
        "h4",
        ".title"
    ],
    "price": [
        ".price",
        ".cost",
        ".amount",
        "[class*='price']",
        "[class*='cost']"
    ],
    "link": [
        "a[href*='product']",
        ".product-link",
        "a"
    ]
}

# Enhanced brand configurations with multiple selector options
ENHANCED_BRAND_CONFIG = {
    "Nishat Linen": {
        "url": "https://nishatlinen.com",
        "search_url": "https://nishatlinen.com/search",
        "search_params": {"type": "product", "q": ""},
        "description": "Premium Pakistani fashion and home textiles",
        "selectors": [
            {
                "product_container": ".grid__item.product-item",
                "image": ".product-item__image-wrapper img",
                "title": ".product-item__title",
                "price": ".price__regular .price-item--regular",
                "link": ".product-item__image-wrapper a"
            },
            {
                "product_container": ".product-card",
                "image": ".product-image img",
                "title": ".product-title",
                "price": ".price",
                "link": ".product-link"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 3
    },
    
    "Khaadi": {
        "url": "https://pk.khaadi.com",
        "search_url": "https://pk.khaadi.com/search",
        "search_params": {"q": ""},
        "description": "Contemporary Pakistani fashion brand",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item a"
            },
            {
                "product_container": ".product-card",
                "image": ".product-card__image img",
                "title": ".product-card__title",
                "price": ".product-card__price",
                "link": ".product-card a"
            }
        ],
        "pagination": ".pagination__item",
        "max_pages": 2
    },
    
    "Gul Ahmed": {
        "url": "https://www.gulahmedshop.com",
        "search_url": "https://www.gulahmedshop.com/advancesearch",
        "search_params": {"search": ""},
        "description": "Leading textile and fashion house",
        "selectors": [
            {
                "product_container": ".item.product.product-item",
                "image": ".product-image-container img",
                "title": ".product-item-link",
                "price": ".price-box .price",
                "link": ".product-item-link"
            },
            {
                "product_container": ".product-item",
                "image": ".product-image img",
                "title": ".product-name",
                "price": ".price",
                "link": ".product-item a"
            }
        ],
        "pagination": ".pages-items a",
        "max_pages": 2
    },
    
    "Sana Safinaz": {
        "url": "https://sanasafinaz.com",
        "search_url": "https://sanasafinaz.com/search",
        "search_params": {"q": ""},
        "description": "High-end Pakistani designer wear",
        "selectors": [
            {
                "product_container": ".grid-product__content",
                "image": ".grid-product__image img",
                "title": ".grid-product__title",
                "price": ".grid-product__price",
                "link": ".grid-product__link"
            },
            {
                "product_container": ".product-card",
                "image": ".product-card__image img",
                "title": ".product-card__info h3",
                "price": ".product-card__price",
                "link": ".product-card a"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    },
    
    "Maria B": {
        "url": "https://www.mariab.pk",
        "search_url": "https://www.mariab.pk/search",
        "search_params": {"q": ""},
        "description": "Designer Pakistani clothing",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item__image-wrapper a"
            },
            {
                "product_container": ".grid__item",
                "image": ".product-form__cart-submit img",
                "title": ".product-single__title",
                "price": ".product-single__prices",
                "link": "a"
            }
        ],
        "pagination": ".pagination__text",
        "max_pages": 2
    },
    
    "Alkaram Studio": {
        "url": "https://alkaramstudio.com",
        "search_url": "https://alkaramstudio.com/search",
        "search_params": {"q": ""},
        "description": "Fashion and lifestyle brand",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image-wrapper img",
                "title": ".product-item__title",
                "price": ".price-item.price-item--regular",
                "link": ".product-item__title"
            },
            {
                "product_container": ".grid-product",
                "image": ".grid-product__image img",
                "title": ".grid-product__title",
                "price": ".grid-product__price",
                "link": ".grid-product__link"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    },
    
    "Cross Stitch": {
        "url": "https://www.crossstitch.pk",
        "search_url": "https://www.crossstitch.pk/search",
        "search_params": {"q": ""},
        "description": "Contemporary Pakistani fashion",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item a"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    },
    
    "Sapphire": {
        "url": "https://pk.sapphireonline.pk",
        "search_url": "https://pk.sapphireonline.pk/search",
        "search_params": {"q": ""},
        "description": "Modern Pakistani fashion brand",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item a"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    },
    
    "Bonanza Satrangi": {
        "url": "https://bonanzasatrangi.com",
        "search_url": "https://bonanzasatrangi.com/search",
        "search_params": {"q": ""},
        "description": "Colorful Pakistani fashion collection",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item a"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    },
    
    "Zara Shahjahan": {
        "url": "https://zarashahjahan.com",
        "search_url": "https://zarashahjahan.com/search",
        "search_params": {"q": ""},
        "description": "Luxury Pakistani designer brand",
        "selectors": [
            {
                "product_container": ".product-item",
                "image": ".product-item__image img",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "link": ".product-item a"
            }
        ],
        "pagination": ".pagination a",
        "max_pages": 2
    }
}

# Common patterns found across Pakistani fashion websites
COMMON_PATTERNS = {
    "price_patterns": [
        r"PKR\s*[\d,]+",
        r"Rs\.?\s*[\d,]+",
        r"₨\s*[\d,]+",
        r"[\d,]+\s*PKR",
        r"[\d,]+\s*Rs",
        r"[\d,]+\s*₨"
    ],
    "image_patterns": [
        r"\.jpg",
        r"\.jpeg", 
        r"\.png",
        r"\.webp"
    ],
    "exclude_keywords": [
        "logo",
        "icon",
        "banner",
        "advertisement",
        "social"
    ]
}

# Categories and their common search terms
CATEGORY_SEARCH_TERMS = {
    "wedding": [
        "bridal", "wedding", "lehenga", "gharara", "sharara", 
        "bride", "nikah", "walima", "heavy dupatta"
    ],
    "party": [
        "party wear", "fancy", "embroidered", "sequin", 
        "evening", "function", "celebration", "gown"
    ],
    "casual": [
        "kurti", "casual", "cotton", "lawn", "everyday", 
        "simple", "comfortable", "daily wear", "basic"
    ],
    "formal": [
        "formal", "office", "professional", "business", 
        "work wear", "corporate", "elegant", "sophisticated"
    ],
    "winter": [
        "winter", "sweater", "cardigan", "jacket", "coat", 
        "warm", "woolen", "fleece", "thermal"
    ],
    "summer": [
        "summer", "lawn", "cotton", "linen", "light", 
        "breathable", "cool", "sleeveless", "shorts"
    ]
}

# Price ranges for different categories (in PKR)
PRICE_RANGES = {
    "budget": {"min": 0, "max": 5000, "label": "Under PKR 5,000"},
    "mid_range": {"min": 5000, "max": 15000, "label": "PKR 5,000 - 15,000"},
    "premium": {"min": 15000, "max": 30000, "label": "PKR 15,000 - 30,000"},
    "luxury": {"min": 30000, "max": 100000, "label": "Above PKR 30,000"}
}

# Headers rotation for different requests
ROTATING_HEADERS = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    },
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
]

# Rate limiting configuration
RATE_LIMITS = {
    "requests_per_minute": 30,
    "delay_between_requests": 2,  # seconds
    "max_concurrent_requests": 3,
    "timeout": 15  # seconds
}