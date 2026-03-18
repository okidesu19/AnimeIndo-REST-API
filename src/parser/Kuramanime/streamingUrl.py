import logging
import asyncio
import random
from fastapi import HTTPException
from Config.config import (
    KURAMANIME_URI, 
    generate_response, 
    responseRq,
    get_proxy_config,
    get_browser_launch_args,
    get_context_options,
    PLAYWRIGHT_STEALTH_SCRIPT
)
from Config.schemas import StreamingQuality, StreamingResponse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List
from ._extract_streaming_data import _extract_streaming_data

# Setup logging
logger = logging.getLogger(__name__)


def streamingUrl(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    """Get streaming URL using requests (default method)."""
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
     
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
        
        if streaming_data:
            logger.info(f"✓ Found {len(streaming_data)} sources via requests")
            return generate_response(200, 'success', {
                "streamingSources": streaming_data,
                "episodeInfo": {
                    "animeId": animeId,
                    "animeSlug": animeSlug,
                    "episodeId": episodeId
                },
                "fetchMethod": "Requests (Default)"
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
    """Get streaming URL using Playwright with proxy support."""
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
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
                launch_args = get_browser_launch_args()
                launch_options = {'headless': True, 'args': launch_args}
                
                # Add proxy if enabled
                if proxy_config.get('enabled'):
                    proxy = {'server': proxy_config['server']}
                    if proxy_config.get('username') and proxy_config.get('password'):
                        proxy['username'] = proxy_config['username']
                        proxy['password'] = proxy_config['password']
                    launch_options['proxy'] = proxy
                    logger.info(f"Using proxy: {proxy_config['server']}")
                
                browser = await p.chromium.launch(**launch_options)
                
                context_options = get_context_options()
                context = await browser.new_context(**context_options)
                
                page = await context.new_page()
                await page.add_init_script(PLAYWRIGHT_STEALTH_SCRIPT)
                
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
