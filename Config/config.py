import requests
import os
import asyncio
import random
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Union, Dict, List
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

OTAKUDESU_URI = 'https://otakudesu.cloud'
KURAMANIME_URI = os.getenv('KURAMANIME_URI')

# Request timeout settings
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
PLAYWRIGHT_TIMEOUT = int(os.getenv('PLAYWRIGHT_TIMEOUT', '45000'))
PLAYWRIGHT_RETRIES = int(os.getenv('PLAYWRIGHT_RETRIES', '3'))

# ==================== USER AGENTS ====================

# User Agents for requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# User Agents for Playwright
PLAYWRIGHT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# ==================== STEALTH SCRIPTS ====================

# Stealth script for Playwright
PLAYWRIGHT_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
window.chrome = { runtime: {} };
window.navigator.chrome = true;
"""

# ==================== REFERER & LANGUAGES ====================

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

LANGUAGES = [
    "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "id,en-US;q=0.8,en;q=0.6",
    "en-US,en;q=1.0,id-ID;q=0.9",
]

# ==================== PROXY CONFIGURATION ====================

def get_proxy_config() -> dict:
    """Get proxy configuration from environment variable PROXY_URL"""
    proxy_url = os.getenv('PROXY_URL', '')
    
    if not proxy_url:
        return {'enabled': False}
    
    try:
        proxy_parts = proxy_url.replace('http://', '').replace('https://', '').split('@')
        
        if len(proxy_parts) == 2:
            credentials, server = proxy_parts
            username, password = credentials.split(':')
            proxy_config = {
                'enabled': True,
                'server': f'http://{server}',
                'username': username,
                'password': password
            }
        else:
            proxy_config = {
                'enabled': True,
                'server': f'http://{proxy_parts[0]}',
                'username': None,
                'password': None
            }
        
        logger.info(f"Proxy enabled: {proxy_config['server']}")
        print(f"Proxy enabled: {proxy_config['server']}")
        return proxy_config
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return {'enabled': False}

# ==================== BROWSER LAUNCH ARGS ====================

def get_browser_launch_args() -> list:
    """Get browser launch arguments for Playwright"""
    return [
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--disable-web-security',
        '--allow-running-insecure-content',
    ]

def get_context_options() -> dict:
    """Get context options for Playwright"""
    proxy_config = get_proxy_config()
    
    options = {
        'viewport': {'width': 1920, 'height': 1080},
        'user_agent': random.choice(PLAYWRIGHT_USER_AGENTS),
        'locale': 'id-ID',
        'timezone_id': 'Asia/Jakarta',
        'permissions': ['geolocation'],
        'extra_http_headers': {
            'Accept-Language': random.choice(LANGUAGES),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': random.choice(REFERER_URLS),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
    }
    
    # Add proxy if enabled
    if proxy_config.get('enabled'):
        proxy = {'server': proxy_config['server']}
        if proxy_config.get('username') and proxy_config.get('password'):
            proxy['username'] = proxy_config['username']
            proxy['password'] = proxy_config['password']
        options['proxy'] = proxy
    
    return options

# ==================== SESSION MANAGEMENT ====================

class EnhancedSession:
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(LANGUAGES),
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache'
        })
        
        logger.info("=== SESSION SETUP DEBUG ===")
    
    def get_random_headers(self, url=None):
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': random.choice(REFERER_URLS) if random.random() > 0.3 else (url if url else "https://www.google.com/"),
        }
        
        if random.random() > 0.7:
            headers['Sec-Ch-Ua'] = f'"Not_ABrand";v="8", "Chromium";v="{random.randint(110, 120)}", "Google Chrome";v="{random.randint(110, 120)}"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = '"Windows"'
        
        return headers
    
    def request_with_retry(self, url, method='GET', **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retry attempt {attempt + 1} for {url} after {delay:.2f}s delay")
                    time.sleep(delay)
                
                headers = kwargs.pop('headers', {})
                headers.update(self.get_random_headers(url))
                
                if random.random() > 0.8:
                    human_delay = random.uniform(0.5, 2.0)
                    logger.info(f"Adding human-like delay of {human_delay:.2f}s")
                    time.sleep(human_delay)
                
                logger.info(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    **kwargs
                )
                
                logger.info(f"Response: {response.status_code} for {url}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url} - attempt {attempt + 1}")
                    if attempt == MAX_RETRIES - 1:
                        raise requests.exceptions.HTTPError(f"403 Forbidden after {MAX_RETRIES} attempts")
                elif response.status_code == 429:
                    logger.warning(f"429 Rate Limited for {url} - attempt {attempt + 1}")
                    if attempt == MAX_RETRIES - 1:
                        raise requests.exceptions.HTTPError(f"429 Rate Limited after {MAX_RETRIES} attempts")
                else:
                    response.raise_for_status()
                    
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                logger.error(f"Request failed for {url} (attempt {attempt + 1}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise
                continue
        
        raise requests.exceptions.HTTPError(f"Failed after {MAX_RETRIES} attempts")

# Global session instance
enhanced_session = EnhancedSession()

# Legacy cookies
cookies = {
    "show_country": "JP", 
    "show_genre": "only_not_hentai"
}

# ==================== RESPONSE FUNCTIONS ====================

def responseRq(url):
    """Enhanced request function with anti-detection"""
    try:
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
    """Generate JSON request headers"""
    return enhanced_session.get_random_headers(url)

def generate_response(status_code: int, message: str, data: Union[Dict, List]):
    return {
        "status": status_code,
        "message": message,
        "data": data
    }

def resolve_safelink(safelink_url):
    """Enhanced safelink resolver"""
    try:
        response = enhanced_session.request_with_retry(safelink_url, allow_redirects=False)
        if 'Location' in response.headers:
            return response.headers['Location']
        else:
            return safelink_url
    except Exception as e:
        logger.error(f"Failed to resolve safelink {safelink_url}: {str(e)}")
        return safelink_url

def health_check():
    """Test the enhanced session"""
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
