import requests
import os
from fastapi.responses import JSONResponse
from typing import Union, Dict, List
import random
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, quote_plus
import os
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OTAKUDESU_URI = 'https://otakudesu.cloud'
KURAMANIME_URI = 'https://v8.kuramanime.tel'

# Enhanced User Agents Pool
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# Referer URLs pool for anti-detection
REFERER_URLS = [
    "https://www.google.com/",
    "https://www.google.co.id/",
    "https://duckduckgo.com/",
    "https://bing.com/",
    "https://www.youtube.com/",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.instagram.com/",
    "",
]

# Language preferences
LANGUAGES = [
    "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "id,en-US;q=0.8,en;q=0.6",
    "en-US,en;q=1.0,id-ID;q=0.9",
]

# Session management
class EnhancedSession:
    def __init__(self):
        self.session = requests.Session()
        self.proxies = None
        self.scraperapi_key = os.getenv('SCRAPERAPI_KEY')
        self.scrapingbee_key = os.getenv('SCRAPINGBEE_KEY')
        # BrightData / Luminati style outbound proxy (explicit env var)
        self.brightdata_proxy = os.getenv('BRIGHTDATA_PROXY')
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with retry strategy and default headers"""
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        



        # Default headers - Force no compression to get raw HTML
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(LANGUAGES),
            'Accept-Encoding': 'identity',  # Disable compression completely
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache'
        })
        # Load proxy from environment if provided (e.g. PROXY_URL="http://user:pass@host:port")
        proxy_url = os.getenv('PROXY_URL') or os.getenv('OUTBOUND_PROXY') or os.getenv('REQUESTS_PROXY')
        if proxy_url:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"Using outbound proxy from environment: {proxy_url}")
        elif self.brightdata_proxy:
            # If BRIGHTDATA_PROXY is provided, prefer it as explicit proxy
            self.proxies = {
                'http': self.brightdata_proxy,
                'https': self.brightdata_proxy
            }
            logger.info(f"Using BrightData/explicit proxy: {self.brightdata_proxy}")
        elif self.scraperapi_key:
            logger.info("No outbound proxy set; ScraperAPI key detected — will use ScraperAPI as fallback.")
        elif self.scrapingbee_key:
            logger.info("No outbound proxy set; ScrapingBee key detected — will use ScrapingBee as fallback.")
    
    def get_random_headers(self, url=None):
        """Generate random headers for request"""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': random.choice(REFERER_URLS) if random.random() > 0.3 else (url if url else "https://www.google.com/"),
        }
        
        # Add random delays for certain headers to appear more human-like
        if random.random() > 0.7:
            headers['Sec-Ch-Ua'] = f'"Not_ABrand";v="8", "Chromium";v="{random.randint(110, 120)}", "Google Chrome";v="{random.randint(110, 120)}"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = '"Windows"'
        
        return headers
    
    def request_with_retry(self, url, method='GET', **kwargs):
        """Make request with retry and anti-detection measures"""
        max_retries = 3
        delay_base = 1
        
        for attempt in range(max_retries):
            try:
                # Add random delay between attempts
                if attempt > 0:
                    delay = delay_base * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retry attempt {attempt + 1} for {url} after {delay:.2f}s delay")
                    time.sleep(delay)
                
                # Get headers
                headers = kwargs.pop('headers', {})
                headers.update(self.get_random_headers(url))
                
                # Add random delay before request (simulate human behavior)
                if random.random() > 0.8:
                    human_delay = random.uniform(0.5, 2.0)
                    logger.info(f"Adding human-like delay of {human_delay:.2f}s")
                    time.sleep(human_delay)
                
                logger.info(f"Making {method} request to {url} (attempt {attempt + 1})")
                


                request_url = url
                # If no proxy configured, check available scraping providers in preference order
                if not self.proxies:
                    if self.brightdata_proxy:
                        # brightdata_proxy should already have been set in proxies, but double-check
                        logger.info("Routing via BrightData proxy")
                    elif self.scraperapi_key:
                        wrapper = f"https://api.scraperapi.com?api_key={self.scraperapi_key}&url={quote_plus(url)}&render=true"
                        logger.info(f"Routing request via ScraperAPI for URL: {url}")
                        request_url = wrapper
                    elif self.scrapingbee_key:
                        wrapper = f"https://app.scrapingbee.com/api/v1?api_key={self.scrapingbee_key}&url={quote_plus(url)}&render_js=true"
                        logger.info(f"Routing request via ScrapingBee for URL: {url}")
                        request_url = wrapper

                response = self.session.request(
                    method=method,
                    url=request_url,
                    headers=headers,
                    timeout=30,
                    proxies=self.proxies,
                    **kwargs
                )
                
                # Ensure response is properly decoded for BeautifulSoup
                if response.status_code == 200:
                    logger.info(f"Response encoding: {response.encoding}")
                    # Force text decoding with explicit encoding
                    if not response.text:
                        logger.warning("Response text is empty, forcing decode")
                        response.raw.decode_content = True
                
                # Log response info
                logger.info(f"Response: {response.status_code} for {url}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    # Log headers/body to help debugging when deployed
                    try:
                        snippet = response.text[:500]
                    except Exception:
                        snippet = '<unavailable body>'
                    logger.warning(f"403 Forbidden for {url} - attempt {attempt + 1} - headers: {response.headers} - body_snippet: {snippet}")
                    if attempt == max_retries - 1:
                        raise requests.exceptions.HTTPError(f"403 Forbidden after {max_retries} attempts")
                elif response.status_code == 429:
                    logger.warning(f"429 Rate Limited for {url} - attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise requests.exceptions.HTTPError(f"429 Rate Limited after {max_retries} attempts")
                else:
                    response.raise_for_status()
                    
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                logger.error(f"Request failed for {url} (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                continue
        
        raise requests.exceptions.HTTPError(f"Failed after {max_retries} attempts")

# Global session instance
enhanced_session = EnhancedSession()

# Legacy cookies (keep for compatibility)
cookies = {
    "show_country": "JP", 
    "show_genre": "only_not_hentai"
}




def responseRq(url):
    """Enhanced request function with anti-detection"""
    try:
        # Set cookies if needed
        kwargs = {}
        if cookies:
            kwargs['cookies'] = cookies
            
        response = enhanced_session.request_with_retry(url, **kwargs)
        return response
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch data from source: {str(e)}"
        )

def headersJson(url):
    """Generate JSON request headers (legacy function)"""
    return enhanced_session.get_random_headers(url)

# generate_response
def generate_response(status_code: int, message: str, data: Union[Dict, List]):
    response_data = {
        "status": status_code,
        "message": message,
        "data": data
    }
    return response_data

def resolve_safelink(safelink_url):
    """Enhanced safelink resolver with better error handling"""
    try:
        response = enhanced_session.request_with_retry(safelink_url, allow_redirects=False)
        if 'Location' in response.headers:
            return response.headers['Location']
        else:
            return safelink_url
    except Exception as e:
        logger.error(f"Failed to resolve safelink {safelink_url}: {str(e)}")
        return safelink_url

# Health check function
def health_check():
    """Test the enhanced session with a simple request"""
    try:
        test_url = f"{KURAMANIME_URI}/"
        response = enhanced_session.request_with_retry(test_url)
        return {
            "status": "healthy",
            "response_code": response.status_code,
            "message": "Connection test successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "message": "Connection test failed"
        }

# Add HTTPException import
from fastapi import HTTPException
