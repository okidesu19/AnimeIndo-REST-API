import re
import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq
from Config.schemas import (
    AnimeViewResponse, PaginatedResponse, OrderBy, ViewType
)

# Setup logging
logger = logging.getLogger(__name__)


def animeView(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
    """Get anime list by view type (ongoing/finished)"""
    anime_data = []
    
    view_mapping = {
        ViewType.ONGOING: "Ongoing",
        ViewType.FINISHED: "Completed"
    }
    VIEW = view_mapping.get(view, "Ongoing")
    
    url = f'{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page={page}'
    
    try:
        response = responseRq(url)
        print(response.text)
        if response.status_code == 403:
            logger.error(f"403 Forbidden accessing anime view endpoint: {url}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to anime view data. The source may be blocking requests from your server. View: {view}, Order: {order_by}, Page: {page}"
            )
        elif response.status_code != 200:
            logger.error(f"Anime view request failed with status {response.status_code}: {url}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch anime view data for {view} (page {page}). Status: {response.status_code}"
            )
        
        # Check if response content is valid
        if not response.text or len(response.text.strip()) < 100:
            logger.warning(f"Anime view response appears empty or too short: {len(response.text)} chars")
            raise HTTPException(
                status_code=502,
                detail=f"Received invalid response from anime view endpoint. The source may be temporarily unavailable."
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in animeView function: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable. Unable to fetch anime view data for {view}: {str(e)}"
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
                anime_view = item.select_one('.view')
                anime_thum = item.select_one('.set-bg')
                anime_name = item.select_one('.sidebar-title-h5')

                # Episode/Star info based on view type
                anime_episode = None
                anime_star = None
                
                if view == ViewType.ONGOING:
                    # For ongoing anime, show episode info
                    episode_star_tag = item.select_one(f'.actual-anime-{anime_id}-ongoing') or item.select_one('.ep span')
                    anime_episode = episode_star_tag.text.strip() if episode_star_tag else None
                elif view == ViewType.FINISHED:
                    # For finished anime, show star info
                    star_tag = item.select_one(f'.actual-anime-{anime_id}')
                    anime_star = star_tag.text.strip() if star_tag else None
                
                anime = AnimeViewResponse(
                    animeId=anime_id,
                    animeSlug=match.group(2),
                    animeName=anime_name.text.strip() if anime_name else 'N/A',
                    animeThum=anime_thum['data-setbg'] if anime_thum else None,
                    animeView=anime_view.text.strip() if anime_view else 'HD',
                    animeStar=anime_star,
                    animeEpisode=anime_episode
                )
                anime_data.append(anime.dict())
        
        return PaginatedResponse(
            status=200,
            message="success",
            data=anime_data,
            pagination={
                "view": VIEW,
                "page": page,
                "maxPage": max_page
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
