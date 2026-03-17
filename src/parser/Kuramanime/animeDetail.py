import re
import logging
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response
from Config.schemas import (
    AnimeDetailResponse, GenreResponse, Episode, PaginationDetail
)
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)


class AnimeDetail:
    """Class to handle anime detail operations using both requests and Playwright."""

    def animeDetailRequest(self, animeId: str, animeSlug: str, page: int = 1) -> Dict:
        """Get anime details by ID and slug using requests."""
        uri = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}?page={page}'
        response = responseRq(uri)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                status=response.status_code,
                message="failed",
                detail="Failed to fetch anime details"
            )
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            details = soup.find('div', class_='col-lg-9').find('div', class_='anime__details__text')
            anime_name = details.find('h3')
            anime_thum = soup.find('div', {'class': 'set-bg'})
            synopsis = details.find('p', id='synopsisField').get_text(strip=True)
            
            def extract_info(label):
                row = details.find('span', text=label).find_parent('div', class_='row')
                data = row.find('div', class_='col-9').text.strip()
                return data if data else None
            
            def extract_genre():
                row = details.find('span', text='Genre:').find_parent('div', class_='row')
                genres_data = []
                for item in row.select('.col-9 > a'):
                    genre_url = item['href']
                    match = re.search(r'genre/([^?]+)', genre_url)
                    if match:
                        genre = GenreResponse(
                            genreName=item.text.strip(),
                            genreSlug=match.group(1)
                        )
                        genres_data.append(genre.dict())
                return genres_data
            
            # Get Episode
            has_next_page = False
            next_page_url = None
            episodes = []
            
            episode_content = soup.find(id="episodeLists").get('data-content', '')
            episode_soup = BeautifulSoup(episode_content, 'html.parser')
            
            for a_tag in episode_soup.find_all('a'):
                eps_url = a_tag.get('href', '').strip().replace(KURAMANIME_URI, "")
                eps_title = ' '.join(a_tag.text.split())
                
                # Skip episodes with "(Terlama)" or "(Terbaru)" in the title
                if eps_url and eps_title.strip() and not ("(Terlama)" in eps_title or "(Terbaru)" in eps_title):
                    # Extract episode number from title
                    ep_num_match = re.search(r'Episode\s+(\d+)', eps_title)
                    ep_num = ep_num_match.group(1) if ep_num_match else "0"
                    
                    episodes.append(Episode(
                        episodeId=eps_url.split('/')[-1],
                        episodeNumber=ep_num,
                        episodeTitle=eps_title,
                        episodeUrl=eps_url
                    ).dict())
                
                # Check for next page marker
                if a_tag == episode_soup.find_all('a')[-1] and not eps_title.strip():
                    has_next_page = True
                    next_page_url = eps_url if eps_url else None
            
            anime_data = AnimeDetailResponse(
                animeId=animeId,
                animeSlug=animeSlug,
                animeName=anime_name.text.strip(),
                animeThum=anime_thum['data-setbg'] if anime_thum else None,
                animeView=extract_info('Kualitas:'),
                animeType=extract_info('Tipe:'),
                animeTotalEpisodes=extract_info('Episode:'),
                animeStatus=extract_info('Status:'),
                animeRelease=extract_info('Musim:').replace('Fall', '').strip(),
                animeDuration=extract_info('Durasi:'),
                animeCountry=extract_info('Negara:'),
                animeAdaptation=extract_info('Adaptasi:'),
                animeSinopsis=synopsis,
                animeGenres=extract_genre(),
                episodes=episodes,
                pagination=PaginationDetail(
                    hasNextPage=has_next_page,
                    nextPageUrl=next_page_url,
                    currentPage=page
                ) if has_next_page else None
            )
            
            return generate_response(200, 'success', anime_data.dict())
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
            raise HTTPException(
                status_code=500, 
                detail=str(e)
            )

    async def animeDetailPlaywright(self, animeId: str, animeSlug: str, page: int = 1) -> Dict:
        """Get anime details by ID and slug using Playwright."""
        uri = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}?page={page}'
        
        logger.info(f"Fetching animeDetail using Playwright: {uri}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page_obj = await browser.new_page()
                await page_obj.goto(uri, wait_until="domcontentloaded", timeout=30000)
                
                html = await page_obj.content()
                await browser.close()
                
            soup = BeautifulSoup(html, 'html.parser')
            details = soup.find('div', class_='col-lg-9').find('div', class_='anime__details__text')
            if not details:
                raise HTTPException(status_code=404, detail="Anime details not found")
            
            anime_name = details.find('h3')
            anime_thum = soup.find('div', {'class': 'set-bg'})
            synopsis = details.find('p', id='synopsisField')
            
            def extract_info(label):
                row = details.find('span', text=label)
                if row:
                    data_div = row.find_parent('div', class_='row').find('div', class_='col-9')
                    return data_div.text.strip() if data_div else None
                return None
            
            def extract_genre():
                genres_data = []
                genre_row = details.find('span', text='Genre:')
                if genre_row:
                    for item in genre_row.find_parent('div', class_='row').select('.col-9 > a'):
                        genre_url = item['href']
                        match = re.search(r'genre/([^?]+)', genre_url)
                        if match:
                            genre = GenreResponse(
                                genreName=item.text.strip(),
                                genreSlug=match.group(1)
                            )
                            genres_data.append(genre.dict())
                return genres_data
            
            episode_content = soup.find(id="episodeLists")
            episodes = []
            has_next_page = False
            next_page_url = None
            
            if episode_content:
                episode_html = episode_content.get('data-content', '')
                episode_soup = BeautifulSoup(episode_html, 'html.parser')
                
                for a_tag in episode_soup.find_all('a'):
                    eps_url = a_tag.get('href', '').strip().replace(KURAMANIME_URI, "")
                    eps_title = ' '.join(a_tag.text.split())
                    
                    if eps_url and eps_title.strip() and not ("(Terlama)" in eps_title or "(Terbaru)" in eps_title):
                        ep_num_match = re.search(r'Episode\\s+(\\d+)', eps_title)
                        ep_num = ep_num_match.group(1) if ep_num_match else "0"
                        
                        episodes.append(Episode(
                            episodeId=eps_url.split('/')[-1],
                            episodeNumber=ep_num,
                            episodeTitle=eps_title,
                            episodeUrl=eps_url
                        ).dict())
                    
                    if a_tag == episode_soup.find_all('a')[-1] and not eps_title.strip():
                        has_next_page = True
                        next_page_url = eps_url if eps_url else None
            
            anime_data = AnimeDetailResponse(
                animeId=animeId,
                animeSlug=animeSlug,
                animeName=anime_name.text.strip() if anime_name else 'N/A',
                animeThum=anime_thum['data-setbg'] if anime_thum else None,
                animeView=extract_info('Kualitas:'),
                animeType=extract_info('Tipe:'),
                animeTotalEpisodes=extract_info('Episode:'),
                animeStatus=extract_info('Status:'),
                animeRelease=extract_info('Musim:').replace('Fall', '').strip() if extract_info('Musim:') else None,
                animeDuration=extract_info('Durasi:'),
                animeCountry=extract_info('Negara:'),
                animeAdaptation=extract_info('Adaptasi:'),
                animeSinopsis=synopsis.get_text(strip=True) if synopsis else None,
                animeGenres=extract_genre(),
                episodes=episodes,
                pagination=PaginationDetail(
                    hasNextPage=has_next_page,
                    nextPageUrl=next_page_url,
                    currentPage=page
                ) if has_next_page else None
            )
            
            return generate_response(200, 'success', anime_data.dict() | {"fetchMethod": "Playwright"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
