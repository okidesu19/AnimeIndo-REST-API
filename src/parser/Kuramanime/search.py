import re
import logging
import asyncio
import random
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response
from Config.schemas import SearchResponse, PaginatedResponse, OrderBy
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


class Search:
    """Class to handle search operations using both requests and Playwright."""

    def searchRequest(self, query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
        """Search anime by query using requests."""
        url = f'{KURAMANIME_URI}/anime?order_by={order_by}&search={query}&page={page}'
        response = responseRq(url)
        anime_data = []
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch search results"
            )
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            max_page = 1
            
            nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
            if nav:
                page_links = nav.find_all('a', href=True)
                for link in page_links:
                    href = link['href']
                    if 'page=' in href:
                        page_number = int(href.split('page=')[-1])
                        if page_number > max_page:
                            max_page = page_number
            
            for item in soup.select('.filter__gallery > a'):
                anime_url = item['href']
                match = re.search(r'anime/(\d+)/(.+)', anime_url)
                if match:
                    anime_id = match.group(1)
                    anime_star = item.select_one(f'.actual-anime-{anime_id}')
                    anime_view = item.select_one('.view')
                    anime_thum = item.select_one('.set-bg')
                    anime_name = item.select_one('.sidebar-title-h5')
                    
                    anime = SearchResponse(
                        animeId=anime_id,
                        animeSlug=match.group(2),
                        animeName=anime_name.text.strip() if anime_name else 'N/A',
                        animeThum=anime_thum['data-setbg'] if anime_thum else None,
                        animeView=anime_view.text.strip() if anime_view else 'HD',
                        animeStar=anime_star.text.strip() if anime_star else None
                    )
                    anime_data.append(anime.dict())
            
            return PaginatedResponse(
                status=200,
                message="success",
                data=anime_data,
                pagination={
                    "page": page,
                    "maxPage": max_page,
                    "query": query,
                    "orderBy": order_by
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    async def searchPlaywright(self, query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
        """Search anime by query using Playwright with anti-detection."""
        url = f'{KURAMANIME_URI}/anime?order_by={order_by}&search={query}&page={page}'
        
        logger.info(f"Searching with Playwright: {url}")
        
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
                
                page_obj = await context.new_page()
                
                await page_obj.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                """)
                
                await page_obj.goto(url, wait_until="networkidle", timeout=45000)
                
                await asyncio.sleep(random.uniform(1, 2))
                
                html = await page_obj.content()
                await browser.close()
                
            soup = BeautifulSoup(html, 'html.parser')
            anime_data = []
            max_page = 1
            
            nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
            if nav:
                page_links = nav.find_all('a', href=True)
                for link in page_links:
                    href = link['href']
                    if 'page=' in href:
                        page_number = int(href.split('page=')[-1])
                        max_page = max(max_page, page_number)
            
            for item in soup.select('.filter__gallery > a'):
                anime_url = item['href']
                match = re.search(r'anime/(\d+)/(.+)', anime_url)
                if match:
                    anime_id = match.group(1)
                    anime_star = item.select_one(f'.actual-anime-{anime_id}')
                    anime_view = item.select_one('.view')
                    anime_thum = item.select_one('.set-bg')
                    anime_name = item.select_one('.sidebar-title-h5')
                    
                    anime = SearchResponse(
                        animeId=anime_id,
                        animeSlug=match.group(2),
                        animeName=anime_name.text.strip() if anime_name else 'N/A',
                        animeThum=anime_thum['data-setbg'] if anime_thum else None,
                        animeView=anime_view.text.strip() if anime_view else 'HD',
                        animeStar=anime_star.text.strip() if anime_star else None
                    )
                    anime_data.append(anime.dict())
            
            return PaginatedResponse(
                status=200,
                message='success',
                data=anime_data,
                pagination={
                    'query': query,
                    'orderBy': order_by,
                    'page': page,
                    'maxPage': max_page,
                    'fetchMethod': 'Playwright'
                }
            )
        except Exception as e:
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))
