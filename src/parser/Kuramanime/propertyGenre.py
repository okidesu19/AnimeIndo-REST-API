import re
import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq
from Config.schemas import SearchResponse, PaginatedResponse, OrderBy

# Setup logging
logger = logging.getLogger(__name__)


def propertyGenre(genre: str, order_by: OrderBy = OrderBy.LATEST, page: str = "1") -> PaginatedResponse:
    """Get anime list by genre"""
    url = f'{KURAMANIME_URI}/properties/genre/{genre}?order_by={order_by}&page={page}'
    response = responseRq(url)
    anime_data = []
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            status=response.status_code,
            message="failed",
            detail="Failed to fetch genre anime list"
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
                "genre": genre,
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
