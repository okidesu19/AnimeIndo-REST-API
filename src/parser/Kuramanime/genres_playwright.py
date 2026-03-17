import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, generate_response
from Config.schemas import GenreResponse
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)

async def genres_playwright() -> Dict:
    """Get all available genres using Playwright (browser automation)"""
    url = f'{KURAMANIME_URI}/properties/genre'
    
    logger.info(f"Fetching genres using Playwright: {url}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
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

