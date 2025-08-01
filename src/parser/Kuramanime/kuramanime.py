import requests
import re
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response, resolve_safelink
from Config.schemas import (
  AnimeViewResponse, GenreResponse, ScheduleResponse,
  SearchResponse, AnimeDetailResponse, StreamingResponse,
  StreamingQuality, Episode, PaginatedResponse,
  OrderBy, Day, ViewType, PaginationDetail
)
import traceback
from playwright.async_api import async_playwright
from typing import Dict, List, Optional

def animeView(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
  anime_data = []
  
  view_mapping = {
    ViewType.ONGOING: "Ongoing",
    ViewType.FINISHED: "Completed"
  }
  VIEW = view_mapping.get(view, "Ongoing")
  
  url = f'{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page={page}'
  response = responseRq(url)
  print(f'header : {response.headers}')
  print(f'cookies : {response.cookies}')
  max_page = 1
  
  if response.status_code != 200:
    raise HTTPException(
      status_code=response.status_code,
      detail="Failed to fetch anime view data"
    )
  
  try:
    soup = BeautifulSoup(response.text, 'html.parser')
    
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
    
    
    for item in soup.select('#animeList > div > a'):
      anime_url = item['href']
      match = re.search(r'/anime/(\d+)/([^/]+)', anime_url)
      if match:
        anime_id = match.group(1)
        anime_star = item.select_one(f'.actual-anime-{anime_id}')  # Perhatikan typo 'anime' vs 'anime'
        anime_episode = item.select_one(f'.actual-anime-{anime_id}-ongoing')
        # print(f"ID: {anime_id}")
#         print(f"Star element: {anime_star}")
#         print(f"Episode element: {anime_episode}")
        anime = SearchResponse(
          animeId=anime_id,
          animeSlug=match.group(2),
          animeName=item.select_one('.sidebar-title-h5').text.strip(),
          animeThum=item.select_one('.set-bg')['data-setbg'],
          animeEpisode=anime_episode.text.strip() if anime_episode else None,
          animeView=item.select_one('.view').text.strip(),
          animeStar=anime_star.text.strip() if anime_star else None
        )
        anime_data.append(anime.dict())
      else:
        print("No match found")
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
  response = responseRq(url)
  anime_data = []
  
  if response.status_code != 200:
    raise HTTPException(
      status_code=response.status_code,
      detail="Failed to fetch schedule data"
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
    try:
        async with async_playwright() as p:  # Gunakan async_playwright
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigasi ke URL dengan timeout yang wajar
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Tunggu elemen video player muncul (jika diperlukan)
            await page.wait_for_selector('#animeVideoPlayer', timeout=10000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Main video player
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
            
            # Alternative servers (jika ada)
            server_list = soup.find('ul', {'id': 'serverList'})
            if server_list:
                for server in server_list.find_all('li'):
                    server_name = server.get('data-name', 'Unknown')
                    server_data = []
                    
                    # Logika untuk ekstrak stream dari setiap server
                    # Contoh sederhana:
                    server_url = f"{url}?server={server_name}"
                    server_data.append(
                        StreamingQuality(
                            quality="HD",
                            url=server_url,
                            type="video/mp4"
                        ).dict()
                    )
                    
                    streaming_data.append(
                        StreamingResponse(
                            server=server_name,
                            videos=server_data
                        ).dict()
                    )
            
            await browser.close()
            
            if streaming_data:
                return generate_response(200, 'success', {
                    "streamingSources": streaming_data,
                    "episodeInfo": {
                        "animeId": animeId,
                        "animeSlug": animeSlug,
                        "episodeId": episodeId
                    }
                })
            return generate_response(404, 'No video sources found', {})
            
    except Exception as e:
        traceback.print_exc()
        if 'browser' in locals():
            await browser.close()
        raise HTTPException(status_code=500, detail=str(e))
