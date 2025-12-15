
import requests
import re
import logging
import os
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response, resolve_safelink, enhanced_session
from Config.schemas import (
  AnimeViewResponse, GenreResponse, ScheduleResponse,
  SearchResponse, AnimeDetailResponse, StreamingResponse,
  StreamingQuality, Episode, PaginatedResponse,
  OrderBy, Day, ViewType, PaginationDetail
)
import traceback
from playwright.async_api import async_playwright
from typing import Dict, List, Optional
import time

# Setup logging
logger = logging.getLogger(__name__)


def animeView(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
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
    traceback.print_exc()
    raise HTTPException(
      status_code=500,
      detail=str(e)
    )

  # print(url)
  # response = responseRq(url)
  # #print(response.text)
  # #print(f'header : {response.headers}')
  # #print(f'cookies : {response.cookies}')
  # max_page = 1
  
  # if response.status_code != 200:
  #   raise HTTPException(
  #     status_code=response.status_code,
  #     detail="Failed to fetch anime view data"
  #   )
  
  # try:
  #   soup = BeautifulSoup(response.text, 'html.parser')
  #   # Find max page (pagination container is .product__pagination)
  #   pagination = soup.select_one('.product__pagination')
  #   if pagination:
  #     page_links = pagination.find_all('a', href=True)
  #     for link in page_links:
  #       href = link['href']
  #       if href and 'page=' in href:
  #         try:
  #           page_number = int(href.split('page=')[-1])
  #           if page_number > max_page:
  #             max_page = page_number
  #         except Exception:
  #           continue

  #   # Each product item is inside an element with class 'product__item'
  #   for product in soup.select('#animeList .product__item'):
  #     # prefer the main anchor (image/title)
  #     anchor = product.find('a', href=True)
  #     if not anchor:
  #       continue
  #     anime_url = anchor['href']
  #     match = re.search(r'/anime/(\d+)/([^/]+)', anime_url)
  #     if not match:
  #       continue

  #     anime_id = match.group(1)

  #     # Name is inside the text block: h5 > a
  #     name_tag = product.select_one('.product__item__text h5 a') or product.select_one('h5 a')

  #     # Thumbnail can be in data-setbg or inline style
  #     thum_tag = product.select_one('.set-bg')
  #     anime_thum = None
  #     if thum_tag:
  #       anime_thum = thum_tag.get('data-setbg') or None
  #       if not anime_thum:
  #         # try to extract from style attribute
  #         style = thum_tag.get('style', '')
  #         m = re.search(r'url\((?:\"|\')?(.*?)(?:\"|\')?\)', style)
  #         if m:
  #           anime_thum = m.group(1)

  #     # Episode info
  #     episode_tag = product.select_one(f'.actual-anime-{anime_id}-ongoing') or product.select_one('.ep span')
  #     anime_episode = episode_tag.text.strip() if episode_tag else None

  #     # Status (SELESAI or hidden)
  #     status_tag = product.select_one('.status span') or product.select_one('.d-none span')
  #     anime_status = status_tag.text.strip() if status_tag else None

  #     # Comments and views
  #     comments_tag = product.select_one(f'.comments-count-{anime_id}-ongoing')
  #     views_tag = product.select_one(f'.views-count-{anime_id}-ongoing')
  #     comments = comments_tag.text.strip() if comments_tag else None
  #     views = views_tag.text.strip() if views_tag else None

  #     # Quality (find anchor that links to properties/quality)
  #     quality_tag = None
  #     for a in product.select('.product__item__text ul a'):
  #       href = a.get('href', '')
  #       if '/properties/quality/' in href:
  #         li = a.find('li')
  #         quality_tag = li.text.strip() if li else a.text.strip()
  #         break

  #     anime = SearchResponse(
  #       animeId=anime_id,
  #       animeSlug=match.group(2),
  #       animeName=name_tag.text.strip() if name_tag else 'N/A',
  #       animeThum=anime_thum,
  #       animeEpisode=anime_episode,
  #       animeView=quality_tag or views,
  #       animeStar=None
  #     )
  #     anime_data.append(anime.dict())
  #   return PaginatedResponse(
  #     status=200,
  #     message="success",
  #     data=anime_data,
  #     pagination={
  #       "view": VIEW,
  #       "page": page,
  #       "maxPage": max_page
  #     }
  #   )
  # except Exception as e:
  #   traceback.print_exc()
  #   raise HTTPException(
  #     status_code=500, 
  #     detail=str(e)
  #   )

def genres() -> Dict:
  url = f'{KURAMANIME_URI}/properties/genre?genre_type=all&page=1'
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
      match = re.search(r'genre/([^?]+)', genre_url)
      if match:
        genre = GenreResponse(
          genreName=item.select_one('a > span').text.strip(),
          genreSlug=match.group(1)
        )
        genres_data.append(genre.dict())
    
    return generate_response(200, 'success', genres_data)
  except Exception as e:
    traceback.print_exc()
    raise HTTPException(
      status_code=500, 
      detail=str(e)
    )


def schedule(day: Day, page: int = 1) -> PaginatedResponse:
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
    traceback.print_exc()
    raise HTTPException(
      status_code=500, 
      detail=str(e)
    )

def search(query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
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
        "query": query,
        "orderBy": order_by
      }
    )
  except Exception as e:
    traceback.print_exc()
    raise HTTPException(
      status_code=500,
      detail=str(e)
    )

def propertyGenre(genre: str, order_by: OrderBy = OrderBy.LATEST, page: str = "1") -> PaginatedResponse:
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
    traceback.print_exc()
    raise HTTPException(
      status_code=500,
      detail=str(e)
    )

def animeDetail(animeId: str, animeSlug: str, page: int = 1) -> Dict:
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
    traceback.print_exc()
    print(e)
    raise HTTPException(
      status_code=500, 
      detail=str(e)
    )

async def streamingUrl(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
    is_serverless = os.getenv('VERCEL') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_NAME')
    
    # Priority 1: Try direct proxy (PROXY_URL, WebShare, SSH tunnel, or BRIGHTDATA_PROXY)
    if enhanced_session.proxies:
        logger.info(f"Attempting to fetch streaming URL via proxy: {url}")
        try:
            response = enhanced_session.request_with_retry(url)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                streaming_data = _extract_streaming_data(soup, url)
                fetch_method = "Proxy (PROXY_URL/WebShare/SSH/BrightData)"
                if streaming_data:
                    logger.info(f"✓ Found {len(streaming_data)} sources via proxy")
                    return generate_response(200, 'success', {
                        "streamingSources": streaming_data,
                        "episodeInfo": {
                            "animeId": animeId,
                            "animeSlug": animeSlug,
                            "episodeId": episodeId
                        },
                        "fetchMethod": fetch_method
                    })
                else:
                    logger.warning(f"✗ Proxy returned 200 but no streaming data extracted from HTML")
        except Exception as e:
            logger.warning(f"Proxy fetch failed: {str(e)}, trying next method...")
    
    # Priority 2: Try ScraperAPI
    if enhanced_session.scraperapi_key and not fetch_method:
        logger.info(f"Attempting to fetch streaming URL via ScraperAPI: {url}")
        try:
            from urllib.parse import quote_plus
            wrapper = f"https://api.scraperapi.com?api_key={enhanced_session.scraperapi_key}&url={quote_plus(url)}&render=true"
            response = enhanced_session.request_with_retry(wrapper)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                streaming_data = _extract_streaming_data(soup, url)
                fetch_method = "ScraperAPI"
                if streaming_data:
                    logger.info(f"✓ Found {len(streaming_data)} sources via ScraperAPI")
                    return generate_response(200, 'success', {
                        "streamingSources": streaming_data,
                        "episodeInfo": {
                            "animeId": animeId,
                            "animeSlug": animeSlug,
                            "episodeId": episodeId
                        },
                        "fetchMethod": fetch_method
                    })
        except Exception as e:
            logger.warning(f"ScraperAPI fetch failed: {str(e)}, trying next method...")
    
    # Priority 3: Try ScrapingBee
    if enhanced_session.scrapingbee_key and not fetch_method:
        logger.info(f"Attempting to fetch streaming URL via ScrapingBee: {url}")
        try:
            from urllib.parse import quote_plus
            wrapper = f"https://app.scrapingbee.com/api/v1?api_key={enhanced_session.scrapingbee_key}&url={quote_plus(url)}&render_js=true"
            response = enhanced_session.request_with_retry(wrapper)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                streaming_data = _extract_streaming_data(soup, url)
                fetch_method = "ScrapingBee"
                if streaming_data:
                    logger.info(f"✓ Found {len(streaming_data)} sources via ScrapingBee")
                    return generate_response(200, 'success', {
                        "streamingSources": streaming_data,
                        "episodeInfo": {
                            "animeId": animeId,
                            "animeSlug": animeSlug,
                            "episodeId": episodeId
                        },
                        "fetchMethod": fetch_method
                    })
        except Exception as e:
            logger.warning(f"ScrapingBee fetch failed: {str(e)}, falling back...")
    
    # Priority 4: Only use Playwright in LOCAL development, NOT in serverless/production
    if is_serverless:
        logger.error(f"✗ Running in serverless environment (Vercel/Railway/Heroku) but no proxy/API key configured")
        error_msg = (
            "Streaming URL fetch failed. No proxy or API key configured for serverless environment. "
            "Please configure one of: PROXY_URL, WEBSHARE_API_KEY, SSH_HOST+SSH_USER+SSH_PASSWORD, "
            "BRIGHTDATA_PROXY, SCRAPERAPI_KEY, or SCRAPINGBEE_KEY. "
            f"For more info, see: https://github.com/okidesu19/AnimeIndo-REST-API#proxy--scraper-fallback-deployment"
        )
        raise HTTPException(status_code=503, detail=error_msg)
    
    # LOCAL DEVELOPMENT ONLY: Fallback to Playwright (not recommended for production)
    logger.info(f"LOCAL DEV: Falling back to Playwright for: {url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigasi ke URL dengan timeout lebih pendek
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Tunggu elemen video player muncul
            try:
                await page.wait_for_selector('#animeVideoPlayer', timeout=5000)
            except:
                logger.warning("Video player selector not found, proceeding anyway")
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            streaming_data = _extract_streaming_data(soup, url)
            await browser.close()
            
            fetch_method = "Playwright"
            if streaming_data:
                logger.info(f"✓ Found {len(streaming_data)} sources via Playwright")
                return generate_response(200, 'success', {
                    "streamingSources": streaming_data,
                    "episodeInfo": {
                        "animeId": animeId,
                        "animeSlug": animeSlug,
                        "episodeId": episodeId
                    },
                    "fetchMethod": fetch_method
                })
            return generate_response(404, 'No video sources found', {})
            
    except Exception as e:
        traceback.print_exc()
        if 'browser' in locals():
            await browser.close()
        logger.error(f"Playwright fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch streaming URL. Error: {str(e)}")

def _extract_streaming_data(soup: BeautifulSoup, url: str) -> List:
    """Helper function to extract streaming data from BeautifulSoup object with multiple fallbacks."""
    streaming_data = []
    
    # Try multiple selector approaches to find video sources
    
    # Approach 1: Standard video player with source tags
    video_player_div = soup.find('div', {'id': 'animeVideoPlayer'})
    if video_player_div:
        video_player = video_player_div.find('video', {'id': 'player'})
        if video_player:
            source_tags = video_player.find_all('source')
            for tag in source_tags:
                if tag.has_attr('src'):
                    streaming_data.append(
                        StreamingQuality(
                            quality=tag.get('size', 'unknown'),
                            url=tag['src'],
                            type=tag.get('type', 'video/mp4')
                        ).dict()
                    )
    
    # Approach 2: Look for iframe with video src
    if not streaming_data:
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if src and ('v8' in src or 'anime' in src or 'video' in src.lower()):
                streaming_data.append(
                    StreamingQuality(
                        quality="Unknown",
                        url=src,
                        type="video/mp4"
                    ).dict()
                )
                break
    
    # Approach 3: Look for data-src or any src attribute in video-related tags
    if not streaming_data:
        video_tags = soup.find_all(['video', 'source'])
        for tag in video_tags:
            src = tag.get('src') or tag.get('data-src')
            if src:
                streaming_data.append(
                    StreamingQuality(
                        quality=tag.get('quality', 'Unknown'),
                        url=src,
                        type=tag.get('type', 'video/mp4')
                    ).dict()
                )
    
    # Approach 4: Look for server list and extract URLs
    server_list = soup.find('ul', {'id': 'serverList'})
    if server_list and not streaming_data:
        for server in server_list.find_all('li'):
            server_name = server.get('data-name', 'Unknown')
            server_url = server.get('data-url') or server.find('a', href=True)
            if server_url:
                streaming_data.append(
                    StreamingResponse(
                        server=server_name,
                        videos=[StreamingQuality(
                            quality="HD",
                            url=server_url if isinstance(server_url, str) else server_url.get('href'),
                            type="video/mp4"
                        ).dict()]
                    ).dict()
                )
    
    # Log what we found for debugging
    logger.info(f"_extract_streaming_data found {len(streaming_data)} sources from {url}")
    if not streaming_data:
        # Log first 500 chars of HTML for debugging
        html_snippet = str(soup)[:500]
        logger.warning(f"No streaming data found. HTML snippet: {html_snippet}")
    
    return streaming_data
