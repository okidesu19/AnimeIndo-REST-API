import logging
import re
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, generate_response
from Config.schemas import PaginatedResponse, Day, ScheduleResponse
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)

async def schedule_playwright(day: Day, page: int = 1) -> PaginatedResponse:
    url = f'{KURAMANIME_URI}/schedule?scheduled_day={day}&page={page}'
    
    logger.info(f"Fetching schedule using Playwright: {url}")
    
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
        
        # Pagination
        nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
        if nav:
            page_links = nav.find_all('a', href=True)
            for link in page_links:
                href = link['href']
                if 'page=' in href:
                    page_number = int(href.split('page=')[-1])
                    max_page = max(max_page, page_number)
        
        # Anime items
        for item in soup.select('.filter__gallery > a'):
            anime_url = item['href']
            import re
            match = re.search(r'anime/(\d+)/(.+)', anime_url)
            if match:
                anime_id = match.group(1)
                anime_name = item.select_one('.sidebar-title-h5')
                anime_episode = item.select_one(f'.actual-schedule-ep-{anime_id}')
                animeEpisode = anime_episode.text.strip() if anime_episode else 'N/A'
                matchEpisode = re.search(r'Ep\s*(\d+)', animeEpisode)
                episode = f"Ep {matchEpisode.group(1)}" if matchEpisode else 'N/A'
                anime_thumb = item.select_one('.set-bg')
                anime_schedule = item.select_one('.view span')
                animeSchedule = anime_schedule.text.strip() if anime_schedule else 'N/A'
                matchTime = re.search(r'\((\d{2}:\d{2} WIB)\)', animeSchedule)
                time = matchTime.group(1) if matchTime else animeSchedule
                
                anime = ScheduleResponse(
                    animeId=anime_id,
                    animeSlug=match.group(2),
                    animeName=anime_name.text.strip() if anime_name else 'N/A',
                    animeEpisode=episode,
                    animeThum=anime_thumb['data-setbg'] if anime_thumb else 'N/A',
                    animeSchedule=time
                )
                anime_data.append(anime.dict())
        
        return PaginatedResponse(
            status=200,
            message='success',
            data=anime_data,
            pagination={
                'day': day,
                'page': page,
                'maxPage': max_page,
                'fetchMethod': 'Playwright'
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

