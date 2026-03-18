import logging
import asyncio
import random
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
    Uses stealth techniques to avoid being blocked.
    """
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
    
    logger.info(f"Fetching streaming URL using Playwright: {url}")
    
    # Random delay to mimic human behavior
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    try:
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
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
            )
            
            # Create context with realistic settings
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
            
            # Create new page
            page = await context.new_page()
            
            # Inject stealth scripts to avoid detection
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add chrome runtime
                window.chrome = { runtime: {} };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Add languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['id-ID', 'id', 'en-US', 'en']
                });
                
                // Prevent automation detection
                window.navigator.chrome = true;
            """)
            
            # Navigate with longer timeout
            await page.goto(url, wait_until="networkidle", timeout=45000)
            
            # Random delay after page load
            await asyncio.sleep(random.uniform(1, 2))
            
            # Scroll to bottom to trigger lazy loading
            await page.evaluate("""window.scrollTo(0, document.body.scrollHeight)""")
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Wait for video player to appear
            try:
                await page.wait_for_selector('#animeVideoPlayer', timeout=10000)
            except:
                logger.warning("Video player selector not found, proceeding anyway")
            
            # Get page content
            html = await page.content()
            
            await browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            streaming_data = _extract_streaming_data(soup, url)
            
            fetch_method = "Playwright"
            if streaming_data:
                logger.info(f"✓ Found {len(streaming_data)} sources via Playwright")
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
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'browser' in locals():
            await browser.close()
        logger.error(f"Playwright fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch streaming URL. Error: {str(e)}")
