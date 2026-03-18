import logging
import asyncio
import random
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
        """Get all available genres using Playwright with anti-detection."""
        url = f'{KURAMANIME_URI}/properties/genre'
        
        logger.info(f"Fetching genres using Playwright: {url}")
        
        # Random delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--window-size=1920,1080',
                    ]
                )
                
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
                
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                """)
                
                await page.goto(url, wait_until="networkidle", timeout=45000)
                
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
                
                return generate_response(200, 'success', {
                    "genres": genres_data,
                    "fetchMethod": "Playwright"
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Playwright genres fetch failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
