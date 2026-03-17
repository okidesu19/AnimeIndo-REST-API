import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response
from Config.schemas import GenreResponse
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)


def genres() -> Dict:
    """Get all available genres"""
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
