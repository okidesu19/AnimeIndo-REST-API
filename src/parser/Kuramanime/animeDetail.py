import re
import logging
import asyncio
import random
import os
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

# Enhanced User Agents for Playwright
PLAYWRIGHT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Stealth script
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
window.chrome = { runtime: {} };
window.navigator.chrome = true;
"""


def get_proxy_config() -> dict:
    """Get proxy configuration from environment variable"""
    proxy_url = os.getenv('PROXY_URL', '')
    
    if not proxy_url:
        return {'enabled': False}
    
    # Parse proxy URL: http://user:pass@proxy-host:port
    try:
        proxy_parts = proxy_url.replace('http://', '').replace('https://', '').split('@')
        
        if len(proxy_parts) == 2:
            credentials, server = proxy_parts
            username, password = credentials.split(':')
            proxy_config = {
                'enabled': True,
                'server': f'http://{server}',
                'username': username,
                'password': password
            }
        else:
            proxy_config = {
                'enabled': True,
                'server': f'http://{proxy_parts[0]}',
                'username': None,
                'password': None
            }
        
        logger.info(f"Proxy enabled: {proxy_config['server']}")
        return proxy_config
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return {'enabled': False}


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
                
                if eps_url and eps_title.strip() and not ("(Terlama)" in eps_title or "(Terbaru)" in eps_title):
                    ep_num_match = re.search(r'Episode\s+(\d+)', eps_title)
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
        """Get anime details by ID and slug using Playwright with enhanced timeout handling."""
        uri = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}?page={page}'
        
        logger.info(f"Fetching animeDetail using Playwright: {uri}")
        
        # Get proxy configuration
        proxy_config = get_proxy_config()
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    logger.info(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
                
                async with async_playwright() as p:
                    # Browser launch arguments
                    launch_args = [
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--window-size=1920,1080',
                    ]
                    
                    launch_options = {'headless': True, 'args': launch_args}
                    
                    # Add proxy if enabled
                    if proxy_config.get('enabled'):
                        proxy = {
                            'server': proxy_config['server']
                        }
                        if proxy_config.get('username') and proxy_config.get('password'):
                            proxy['username'] = proxy_config['username']
                            proxy['password'] = proxy_config['password']
                        launch_options['proxy'] = proxy
                        logger.info(f"Using proxy: {proxy_config['server']}")
                    
                    browser = await p.chromium.launch(**launch_options)
                    
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent=random.choice(PLAYWRIGHT_USER_AGENTS),
                        locale='id-ID',
                        timezone_id='Asia/Jakarta',
                        permissions=['geolocation'],
                        extra_http_headers={
                            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                            'Referer': 'https://www.google.com/',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                        }
                    )
                    
                    page_obj = await context.new_page()
                    
                    # Inject stealth scripts
                    await page_obj.add_init_script(STEALTH_SCRIPT)
                    
                    # Use domcontentloaded - faster than networkidle
                    await page_obj.goto(uri, wait_until="domcontentloaded", timeout=45000)
                    
                    # Random delay
                    await asyncio.sleep(random.uniform(1, 2))
                    
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
                
                fetch_method = "Playwright"
                if proxy_config.get('enabled'):
                    fetch_method = "Playwright + Proxy"
                
                return generate_response(200, 'success', anime_data.dict() | {
                    "fetchMethod": fetch_method,
                    "proxyEnabled": proxy_config.get('enabled', False)
                })
            
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                continue
        
        raise HTTPException(
            status_code=504, 
            detail=f"Playwright timeout after {max_retries} attempts: {last_error}. Try using requests method instead."
        )
