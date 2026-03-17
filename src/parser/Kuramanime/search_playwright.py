import re
import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, generate_response
from Config.schemas import PaginatedResponse, OrderBy
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)

async def search_playwright(query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
    url = f'{KURAMANIME_URI}/anime?order_by={order_by}&search={query}&page={page}'
    
    logger.info(f"Searching with Playwright: {url}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page_obj = await browser.new_page()
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            html = await page_obj.content()
            await browser.close()
            
        soup = BeautifulSoup(html, 'html.parser')
        anime_data = []
        max_page = 1
        
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

