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
