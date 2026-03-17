import re
import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq
from Config.schemas import ScheduleResponse, PaginatedResponse, Day

# Setup logging
logger = logging.getLogger(__name__)


def schedule(day: Day, page: int = 1) -> PaginatedResponse:
    """Get anime schedule by day"""
    url = f'{KURAMANIME_URI}/schedule?scheduled_day={day}&page={page}'
    anime_data = []
    
    try:
        response = responseRq(url)
        
        if response.status_code == 403:
            logger.error(f"403 Forbidden accessing schedule endpoint: {url}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to schedule data. The source may be blocking requests from your server. Day: {day}, Page: {page}"
            )
        elif response.status_code != 200:
            logger.error(f"Schedule request failed with status {response.status_code}: {url}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch schedule data for {day} (page {page}). Status: {response.status_code}"
            )
        
        # Check if response content is valid
        if not response.text or len(response.text.strip()) < 100:
            logger.warning(f"Schedule response appears empty or too short: {len(response.text)} chars")
            raise HTTPException(
                status_code=502,
                detail=f"Received invalid response from schedule endpoint. The source may be temporarily unavailable."
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in schedule function: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable. Unable to fetch schedule data for {day}: {str(e)}"
        )
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        max_page = 1
        
        # Find max page
        nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
        if nav:
            page_links = nav.find_all('a', href=True)
            for link in page_links:
                href = link['href']
                if 'page=' in href:
                    page_number = int(href.split('page=')[-1])
                    if page_number > max_page:
                        max_page = page_number
        
        # Parse anime items
        for item in soup.select('.filter__gallery > a'):
            anime_url = item['href']
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
            message="success",
            data=anime_data,
            pagination={
                "page": page,
                "maxPage": max_page,
                "day": day
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=str(e)
        )
