import logging
import asyncio
import random
import os
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response
from Config.schemas import GenreResponse
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)

# Enhanced User Agents for Playwright
PLAYWRIGHT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Stealth script
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
window.chrome = { runtime: {} };
"""


def get_proxy_config() -> dict:
    """Get proxy configuration from environment variable"""
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
        return proxy_config
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return {'enabled': False}


class Genres:
    """Class to handle genres operations using both requests and Playwright."""

    def genresRequest(self) -> Dict:
        """Get all available genres using requests."""
        url = f'{KURAMANIME_URI}/properties/genre'
        response = responseRq(url)
        
        genres_data = []
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch genre data"
            )
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            for item in soup.select('.kuramanime__genres > ul > li'):
                genre_url = item.select_one('a')['href']
                import re
                match = re.search(r'genre/([^?]+)', genre_url)
                if match:
                    genre = GenreResponse(
                        genreName=item.select_one('a > span').text.strip(),
                        genreSlug=match.group(1)
                    )
                    genres_data.append(genre.dict())
            
            return generate_response(200, 'success', genres_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=str(e)
            )

    async def genresPlaywright(self) -> Dict:
        """Get all available genres using Playwright with proxy support."""
        url = f'{KURAMANIME_URI}/properties/genre'
        
        logger.info(f"Fetching genres using Playwright: {url}")
        
        proxy_config = get_proxy_config()
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    logger.info(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
                
                async with async_playwright() as p:
                    launch_args = [
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--window-size=1920,1080',
                    ]
                    
                    launch_options = {'headless': True, 'args': launch_args}
                    
                    if proxy_config.get('enabled'):
                        proxy = {'server': proxy_config['server']}
                        if proxy_config.get('username') and proxy_config.get('password'):
                            proxy['username'] = proxy_config['username']
                            proxy['password'] = proxy_config['password']
                        launch_options['proxy'] = proxy
                    
                    browser = await p.chromium.launch(**launch_options)
                    
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent=random.choice(PLAYWRIGHT_USER_AGENTS),
                        locale='id-ID',
                        timezone_id='Asia/Jakarta',
                        extra_http_headers={
                            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Referer': 'https://www.google.com/',
                        }
                    )
                    
                    page = await context.new_page()
                    await page.add_init_script(STEALTH_SCRIPT)
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    html = await page.content()
                    await browser.close()
                    
                soup = BeautifulSoup(html, 'html.parser')
                genres_data = []
                
                for item in soup.select('.kuramanime__genres > ul > li'):
                    genre_url = item.select_one('a')['href']
                    import re
                    match = re.search(r'genre/([^?]+)', genre_url)
                    if match:
                        genre = GenreResponse(
                            genreName=item.select_one('a > span').text.strip(),
                            genreSlug=match.group(1)
                        )
                        genres_data.append(genre.dict())
                
                fetch_method = "Playwright"
                if proxy_config.get('enabled'):
                    fetch_method = "Playwright + Proxy"
                
                return generate_response(200, 'success', {
                    "genres": genres_data,
                    "fetchMethod": fetch_method,
                    "proxyEnabled": proxy_config.get('enabled', False)
                })
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                continue
        
        raise HTTPException(
            status_code=504,
            detail=f"Playwright timeout after {max_retries} attempts: {last_error}"
        )
