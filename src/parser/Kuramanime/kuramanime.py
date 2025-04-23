import requests
import re
from bs4 import BeautifulSoup
from flask import request
from Config.config import KURAMANIME_URI, responseRq, headersJson, cookies, generete_response, resolve_safelink
from utils.kraken.kraken import Kraken
import traceback
from playwright.sync_api import sync_playwright

#animeView
import requests
from bs4 import BeautifulSoup
import re
import traceback

def animeView(view, order_by):
  animeDATA = []
  if view == 'ongoing' or view == 'finished':
    VIEW = ''
    if view == 'ongoing':
      VIEW = 'Ogoing'
    elif view == 'finished':
      VIEW = 'Completed'
    
    url = f'{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page=1'
    response = responseRq(url)
    print(response.request.headers)
    print(f"{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page=1")
    statusCode = response.status_code
    try:
      if statusCode == 200:
        SOUP = BeautifulSoup(response.text, 'html.parser')
        animeList = SOUP.find('div', {'id': 'animeList'})
        for item in SOUP.select('.filter__gallery > a'):
          anime_url = item['href']
          match = re.search(r'/anime/(\d+)/([^/]+)/', anime_url)
          if match:
            anime = {
              'animeName': item.select_one('.sidebar-title-h5').text.strip(),
              'animeEpisode': item.select_one('.ep span').text.strip(),
              'animeThum': item.select_one('.set-bg')['data-setbg'],
              'animeSlug': match.group(2),
              'animeId': match.group(1),
              'animeView': item.select_one('.view').text.strip()
            }
            animeDATA.append(anime)
        DATA = generete_response(statusCode, 'sukses', animeDATA)
        DATA['view'] = VIEW
        return DATA
      else:
        return generete_response(statusCode, 'gagal', animeDATA)
    except Exception as e:
      traceback.print_exc()
      return generete_response(statusCode, 'error', animeDATA)
  else:
    return {
      'error': 'view not found'
    }
    print('view not found')

#animeGenre
def genres():
  url = f'{KURAMANIME_URI}/properties/genre?genre_type=all&page=1'
  response = responseRq(url)
  genresDATA = []
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      for item in SOUP.select('.kuramanime__genres > ul > li'):
        genre_url = item.select_one('a')['href']
        match = re.search(r'genre/([^?]+)', genre_url)
        if match:
          data = {
            'genreName' : item.select_one('a > span').text.strip(),
            'genreSlug' : match.group(1)
          }
          genresDATA.append(data)
      return generete_response(statusCode, 'sukses', genresDATA)
    else:
      return generete_response(statusCode, 'gagal', genresDATA)
  except Exception as e:
    traceback.print_exc()
    return generete_response(statusCode, 'error', genresDATA)
 
#shedule
def shedule(hari, page):
  url = f'{KURAMANIME_URI}/schedule?scheduled_day={hari}&page={page}'
  response = responseRq(url)
  animeDATA = []
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      max_page = 1
      try:
        nav = SOUP.find('nav', {'aria-label': 'Pagination Navigation'})
        page_links = nav.find_all('a', href=True)
        for link in page_links:
          href = link['href']
          if 'page=' in href:
            page_number = int(href.split('page=')[-1])
            if page_number > max_page:
              max_page = page_number
      except: max_page = 1
      for item in SOUP.select('.filter__gallery > a'):
        anime_url = item['href']
        match = re.search(r'anime/(\d+)/(.+)', anime_url)
        if match:
          anime_id = match.group(1)
          anime_name = item.select_one('.sidebar-title-h5')
          anime_episode = item.select_one(f'.actual-schedule-ep-{anime_id}')
          anime_thumb = item.select_one('.set-bg')
          anime_schedule = item.select_one('.view span')
          anime = {
            'animeName': anime_name.text.strip() if anime_name else 'N/A',
            'animeEpisode': anime_episode.text.strip() if anime_episode else 'N/A',
            'animeThum': anime_thumb['data-setbg'] if anime_thumb else 'N/A',
            'animeSlug': match.group(2),
            'animeId' : anime_id,
            'animeShedule': anime_schedule.text.strip() if anime_schedule else 'N/A'
          }
          animeDATA.append(anime)
      DATA = generete_response(statusCode, 'sukses', animeDATA)
      DATA['page'] = page
      DATA['maxPage'] = max_page
      return DATA
    else :
      return generete_response(statusCode, 'gagal', animeDATA)
  except Exception as e:
    traceback.print_exc()
    return generete_response(statusCode, 'error', animeDATA)

#search
def search(kwy, order_by, page):
  url = f'{KURAMANIME_URI}/anime?order_by={order_by}&search={kwy}&page={page}'
  response = responseRq(url)
  statusCode = response.status_code
  animeDATA = []
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      max_page = 1
      try:
        nav = SOUP.find('nav', {'aria-label': 'Pagination Navigation'})
        page_links = nav.find_all('a', href=True)
        for link in page_links:
          href = link['href']
          if 'page=' in href:
            page_number = int(href.split('page=')[-1])
            if page_number > max_page:
              max_page = page_number
      except: max_page = 1
      
      for item in SOUP.select('.filter__gallery > a'):
        anime_url = item['href']
        match = re.search(r'anime/(\d+)/(.+)', anime_url)
        if match:
          anime_id = match.group(1)
          anime_star = item.select_one(f'.actual-anime-{anime_id}')
          anime_view = item.select_one('.view')
          anime_thum = item.select_one('.set-bg')
          anime_name = item.select_one('.sidebar-title-h5')
          data = {
            'animeName' : anime_name.text.strip() if anime_name else 'N/A',
            'animeThum' : anime_thum['data-setbg'] if anime_thum else None,
            'animeView' : anime_view.text.strip() if anime_view else 'HD',
            'animeStar' : anime_star.text.strip() if anime_star else None,
            'animeSlug' : match.group(2),
            'animeId' : anime_id
          }
          animeDATA.append(data)
      DATA = generete_response(statusCode, 'sukses', animeDATA)
      DATA['page'] = page
      DATA['maxPage'] = max_page
      return DATA
    else:
      return generete_response(statusCode, 'gagal', animeDATA)
  except Exception as e:
    traceback.print_exc()
    return generete_response(statusCode, 'error', animeDATA)

#properties genres
def propertyGenre(genre, order_by, page):
  url = f'{KURAMANIME_URI}/properties/genre/{genre}?order_by={order_by}&page={page}'
  response = responseRq(url)
  animeDATA = []
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      max_page = 1
      try:
        nav = SOUP.find('nav', {'aria-label': 'Pagination Navigation'})
        page_links = nav.find_all('a', href=True)
        for link in page_links:
          href = link['href']
          if 'page=' in href:
            page_number = int(href.split('page=')[-1])
            if page_number > max_page:
              max_page = page_number
      except: max_page = 1
      
      for item in SOUP.select('.filter__gallery > a'):
        anime_url = item['href']
        match = re.search(r'anime/(\d+)/(.+)', anime_url)
        if match:
          anime_id = match.group(1)
          anime_star = item.select_one(f'.actual-anime-{anime_id}')
          anime_view = item.select_one('.view')
          anime_thum = item.select_one('.set-bg')
          anime_name = item.select_one('.sidebar-title-h5')
          data = {
            'animeName' : anime_name.text.strip() if anime_name else 'N/A',
            'animeThum' : anime_thum['data-setbg'] if anime_thum else None,
            'animeView' : anime_view.text.strip() if anime_view else 'HD',
            'animeStar' : anime_star.text.strip() if anime_star else None,
            'animeSlug' : match.group(2),
            'animeId' : anime_id
          }
          animeDATA.append(data)
      DATA = generete_response(statusCode, 'sukses', animeDATA)
      DATA['page'] = page
      DATA['maxPage'] = max_page
      return DATA
    else:
      return generete_response(statusCode, 'gagal', animeDATA)
  except Exception as e:
    traceback.print_exc()
    return generete_response(statusCode, 'error', animeDATA)

#animeDetail
def animeDetail(animeId, animeSlug):
  page = request.args.get('page', '1')
  uri = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}?page={page}'
  response = responseRq(uri)
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      details = SOUP.find('div', class_='col-lg-9').find('div', class_='anime__details__text')
      anime_name = details.find('h3')
      anime_thum = SOUP.find('div', {'class' : 'set-bg'})
      synopsis = details.find('p', id='synopsisField').get_text(strip=True)
      def extract_info(label):
        row = details.find('span', text=label).find_parent('div', class_='row')
        data = row.find('div', class_='col-9').text.strip()
        return data if data else None
      def extract_genre(label):
        row = details.find('span', text=label).find_parent('div', class_='row')
        genresDATA = []
        for item in row.select('.col-9 > a'):
          genre_url = item['href']
          match = re.search(r'genre/([^?]+)', genre_url)
          if match:
            data = {
              'genreName' : item.text.strip(),
              'genreSlug' : match.group(1)
            }
            genresDATA.append(data)
        return genresDATA
        
      #Get Episode
      has_next_page = False
      has_next_link = None
      
      episode_lists = []
      episode_content = SOUP.find(id="episodeLists").get('data-content', '')
      episode_soup = BeautifulSoup(episode_content, 'html.parser')
      
      for a_tag in episode_soup.find_all('a'):
        eps = a_tag.get('href', '').strip().replace(KURAMANIME_URI, "")
        eps_title = ' '.join(a_tag.text.split())
        # Skip episodes with "(Terlama)" or "(Terbaru)" in the title
        if eps and eps_title.strip() and not ("(Terlama)" in eps_title or "(Terbaru)" in eps_title):
          episode_lists.append({
            "episodeId": eps,
            "epsTitle": eps_title
          })
        
        # Check for next page marker
        if a_tag == episode_soup.find_all('a')[-1] and not eps_title.strip():
          has_next_page = True
          has_next_link = eps if eps else None

      
      animeDATA = {
        'animeName' : anime_name.text.strip(),
        'animeThum' : anime_thum['data-setbg'] if anime_thum else None,
        'animeView' : extract_info('Kualitas:'),
        'animeType' : extract_info('Tipe:'),
        'animeEpisode' : extract_info('Episode:'),
        'animeStatus' : extract_info('Status:'),
        'animeRelease' : extract_info('Musim:').replace('Fall', '').strip(),
        'animeDuration' : extract_info('Durasi:'),
        'animeCountry' : extract_info('Negara:'),
        'animeAdaptation' : extract_info('Adaptasi:'),
        'animeSinopsis' : synopsis,
        'animeGenres' : extract_genre('Genre:'),
        'animeEpisode' : episode_lists,
        'has_next_link' : has_next_link,
        'has_next_page' : has_next_page
      }
      return generete_response(statusCode, 'sukses', animeDATA)
    else:
      return generete_response(statusCode, 'gagal', {})
  except Exception as e:
    traceback.print_exc()
    return generete_response(statusCode, 'error', {})


#getStreaming
def streamingUrl(animeId, animeSlug, episode):
  url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episode}'
  streaming_list = []
  print(url)
  try:
    with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto(url, wait_until="networkidle")
      html = page.content()
      SOUP = BeautifulSoup(html, 'html.parser')
      video_player_div = SOUP.find('div', {'id': 'animeVideoPlayer'})
      if video_player_div:
        video_player = video_player_div.find('video', {'id': 'player'})
        if video_player:
          source_tags = video_player.find_all('source')
          for tag in source_tags:
            if tag.has_attr('src'):
              streaming_list.append({
                'streamingUrl': tag['src'],
                'quality': tag.get('size', 'unknown'),  # gunakan get() untuk fallback
                'type': tag.get('type', 'video/mp4')   # default type
              })
      browser.close()
      if streaming_list:
        return generete_response(200, 'sukses', streaming_list)
      else:
        return generate_response(404, 'Sumber video tidak ditemukan', {})
  except Exception as e:
    traceback.print_exc()
    browser.close()
    return generete_response(500, 'error', {})