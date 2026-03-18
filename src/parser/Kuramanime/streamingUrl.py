import logging
import asyncio
import random
import os
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, generate_response, responseRq
from Config.schemas import StreamingQuality, StreamingResponse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List
from ._extract_streaming_data import _extract_streaming_data

# Setup logging
logger = logging.getLogger(__name__)

# Enhanced User Agents for Playwright
PLAYWRIGHT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Stealth script
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
window.chrome = { runtime: {} };
window.navigator.chrome = true;
"""


def get_proxy_config() -> dict:
    """Get proxy configuration from environment variable"""
    proxy_url = os.getenv('PROXY_URL', '')
    
    if not proxy_url:
        return {'enabled': False}
    
    # Parse proxy URL: http://user:pass@proxy-host:port
    try:
        # Remove http:// or https:// prefix
        proxy_parts = proxy_url.replace('http://', '').replace('https://', '').split('@')
        
        if len(proxy_parts) == 2:
            # Has credentials
            credentials, server = proxy_parts
            username, password = credentials.split(':')
            proxy_config = {
                'enabled': True,
                'server': f'http://{server}',
                'username': username,
                'password': password
            }
        else:
            # No credentials
            proxy_config = {
                'enabled': True,
                'server': f'http://{proxy_parts[0]}',
                'username': None,
                'password': None
            }
        
        logger.info(f"Proxy enabled: {proxy_config['server']}")
        return proxy_config
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return {'enabled': False}


def streamingUrl(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    """
    Default method to get streaming URL for an episode using requests + BeautifulSoup.
    This is the default/fallback method.
    """
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
     
    logger.info(f"Fetching streaming URL using requests (default): {url}")
    try:
        response = responseRq(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch streaming URL: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch streaming URL. Status: {response.status_code}"
            )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        streaming_data = _extract_streaming_data(soup, url)
        
        fetch_method = "Requests (Default)"
        if streaming_data:
            logger.info(f"✓ Found {len(streaming_data)} sources via requests")
            return generate_response(200, 'success', {
                "streamingSources": streaming_data,
                "episodeInfo": {
                    "animeId": animeId,
                    "animeSlug": animeSlug,
                    "episodeId": episodeId
                },
                "fetchMethod": fetch_method
            })
        return generate_response(404, 'No video sources found', {})
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Requests fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch streaming URL. Error: {str(e)}")


async def streamingUrlPlaywright(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    """
    Method to get streaming URL for an episode using Playwright.
    Uses enhanced timeout handling and retry logic.
    """
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
    
    logger.info(f"Fetching streaming URL using Playwright: {url}")
    
    # Get proxy configuration
    proxy_config = get_proxy_config()
    
    # Random delay to mimic human behavior
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = random.uniform(2, 5) * (attempt + 1)
                logger.info(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
                await asyncio.sleep(delay)
            
            async with async_playwright() as p:
                # Browser launch arguments
                launch_args = [
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
                
                launch_options = {'headless': True, 'args': launch_args}
                
                # Add proxy if enabled
                if proxy_config.get('enabled'):
                    proxy = {
                        'server': proxy_config['server']
                    }
                    if proxy_config.get('username') and proxy_config.get('password'):
                        proxy['username'] = proxy_config['username']
                        proxy['password'] = proxy_config['password']
                    launch_options['proxy'] = proxy
                    logger.info(f"Using proxy: {proxy_config['server']}")
                
                browser = await p.chromium.launch(**launch_options)
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=random.choice(PLAYWRIGHT_USER_AGENTS),
                    locale='id-ID',
                    timezone_id='Asia/Jakarta',
                    permissions=['geolocation'],
                    extra_http_headers={
                        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Referer': 'https://www.google.com/',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = await context.new_page()
                
                # Inject stealth scripts
                await page.add_init_script(STEALTH_SCRIPT)
                
                # Use domcontentloaded - faster than networkidle
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Random delay after page load
                await asyncio.sleep(random.uniform(1, 2))
                
                # Scroll to trigger lazy loading
                await page.evaluate("""window.scrollTo(0, document.body.scrollHeight)""")
                await asyncio.sleep(random.uniform(0.5, 1))
                
                # Wait for video player
                try:
                    await page.wait_for_selector('#animeVideoPlayer', timeout=10000)
                except:
                    logger.warning("Video player selector not found, proceeding anyway")
                
                html = await page.content()
                await browser.close()
                
                soup = BeautifulSoup(html, 'html.parser')
                streaming_data = _extract_streaming_data(soup, url)
                
                fetch_method = "Playwright"
                if proxy_config.get('enabled'):
                    fetch_method = "Playwright + Proxy"
                
                if streaming_data:
                    logger.info(f"✓ Found {len(streaming_data)} sources via Playwright")
                    return generate_response(200, 'success', {
                        "streamingSources": streaming_data,
                        "episodeInfo": {
                            "animeId": animeId,
                            "animeSlug": animeSlug,
                            "episodeId": episodeId
                        },
                        "fetchMethod": fetch_method,
                        "proxyEnabled": proxy_config.get('enabled', False)
                    })
                return generate_response(404, 'No video sources found', {})
                
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            continue
    
    raise HTTPException(
        status_code=504, 
        detail=f"Playwright timeout after {max_retries} attempts: {last_error}. Try using requests method instead."
    )
