import requests
import re
from bs4 import BeautifulSoup
from Config.config import OTAKUDESU_URI, headers, generete_response, resolve_safelink
from utils.kraken.kraken import Kraken
import traceback

# @ ongoing data
def ongoing():
  animeDATA = []
  response = requests.get(f"{OTAKUDESU_URI}/ongoing-anime/", headers=headers)
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      body = SOUP.find('div', {'class' : 'venz'}).find('ul')
      for list in body.findAll('li'):
        animeEpisode = list.find('div', {'class' : 'epz'}).getText()
        animeDay = list.find('div', {'class' : 'epztipe'}).getText()
        animeRelease = list.find('div', {'class' : 'newnime'}).getText()
        animeSlug = list.find('div', {'class' : 'thumb'}).find('a')['href'].replace(f"{OTAKUDESU_URI}/anime/", "")
        animeThum = list.find('div', {'class' : 'thumb'}).find('div', {'class' : 'thumbz'}).find('img')['src']
        animeName = list.find('div', {'class' : 'thumb'}).find('div', {'class' : 'thumbz'}).find('h2', {'class' : 'jdlflm'}).getText()
        data_info = {
          'animeEpisode' : animeEpisode,
          'animeDay' : animeDay,
          'animeRelease' : animeRelease,
          'animeSlug' : animeSlug,
          'animeThum' : animeThum,
          'animeName' : animeName
        }
        animeDATA.append(data_info)
      return generete_response(statusCode, 'sukses', animeDATA)
    else:
      return generete_response(statusCode, 'gagal', animeDATA)
  except Exception as e:
    import traceback
    traceback.print_exc()
    return generete_response(statusCode, 'error', animeDATA)
  
# genres
def genres():
  genresDATA = []
  response = requests.get(f"{OTAKUDESU_URI}/genre-list/", headers=headers)
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      body = SOUP.find('ul', {'class' : 'genres'})
      print(body.text)
      for list in body.findAll('a'):
        genreName = list.getText()
        genreSlug = list['href'].replace(f"{OTAKUDESU_URI}/genres/", '')
        data_info = {
          'genreName' : genreName,
          'genreSlug' : genreSlug
        }
        genresDATA.append(data_info)
      return generete_response(statusCode, 'sukses', genresDATA)
    else:
      return generete_response(statusCode, 'gagal', genresDATA)
  except Exception as e:
    import traceback
    traceback.print_exc()
    return generete_response(statusCode, 'error', genresDATA)

# Detail anime
def detail(animeSlug):
  response = requests.get(f"{OTAKUDESU_URI}/anime/{animeSlug}", headers=headers)
  statusCode = response.status_code
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      infozin = SOUP.find('div', {'class' : 'infozin'})
      recommend_data = []
      recommend_anime = SOUP.find('div', {'class': 'isi-recommend-anime-series'})
      if recommend_anime:  # Pastikan bahwa recommend_anime tidak None
        for recom in recommend_anime.findAll('div', {'class': 'isi-konten'}):
          animeSlug = recom.find('a')['href'].replace(f'{OTAKUDESU_URI}/anime/', '')
          animeThum = recom.find('a').find('img')['src']
          animeName = recom.find('span').find('a').getText()
          infoData = {
            'animeName': animeName,
            'animeThum': animeThum,
            'animeSlug': animeSlug
          }
          recommend_data.append(infoData)
      else:
        print("Tidak ditemukan elemen dengan class 'isi-recommend-anime-series'")
        
      if infozin:
        infozingle = infozin.find('div', {'class' : 'infozingle'})
        if infozingle:
          data_info = {}
          genre_list = []
          for p in infozingle.findAll('p'):
            span = p.find('span')
            if span:
              text = span.get_text(strip=True)
              if text:
                parts = text.split(':', 1)
                if len(parts) == 2:
                  label = parts[0].strip()
                  value = parts[1].strip()
                  if label == 'Genre':
                    for a in span.find_all('a'):
                      genre_list.append({
                        'genreSlug': a['href'].replace(f"{OTAKUDESU_URI}/genres/", ''),
                        'genreName': a.get_text(strip=True)
                      })
                  else:
                    label_map = {
                      'Judul': 'animeName',
                      'Japanese': 'animeJapanese',
                      'Skor': 'animeScore',
                      'Produser': 'animeProducer',
                      'Tipe': 'animeType',
                      'Status': 'animeStatus',
                      'Total Episode': 'animeTotalEpisodes',
                      'Durasi': 'animeDuration',
                      'Tanggal Rilis': 'animeReleaseDate',
                      'Studio': 'animeStudio'
                    }
                    data_info[label_map.get(label, label)] = value
          
          animeName = data_info['animeName']
          animeThum = SOUP.find('div', {'class' : 'fotoanime'}).find('img')['src']
          sinopsis_element = SOUP.find("div", class_="sinopc")
          if sinopsis_element:
            animeSinopsis = sinopsis_element.text.strip()
          else:
            animeSinopsis = ''
          #Episode
          episode_list = SOUP.findAll('div', {'class' : 'episodelist'})
          episodeDATA = []
          for episode in episode_list:
            title_element = episode.find('div', {'class' : 'smokelister'}).find('span', {'class' : 'monktit'})
            if title_element and 'Episode List' in title_element.text:
              title = title_element.text.strip()
              ul_element = episode.find('ul')
              if ul_element:
                for li in ul_element.find_all('li'):
                  a_element = li.find('a')
                  date_element = li.find('span', {'class' : 'zeebr'})
                  if a_element and date_element:
                    episode_name = a_element.text.strip()
                    episode_name = episode_name.replace('Subtitle Indonesia', '').replace(animeName, '').strip()
                    eps_info = {
                      #'title': title,
                      'episodeName': episode_name,
                      'episodeSlug': a_element['href'].replace(f"{OTAKUDESU_URI}/episode/", ''),
                      'releaseDate': date_element.text.strip()
                    }
                    episodeDATA.append(eps_info)
          
          data_info['animeGenres'] = genre_list
          data_info['animeEpisode'] = episodeDATA
          data_info['animeThum'] = animeThum
          data_info['animeSinopsis'] = animeSinopsis
          data_info['animeRecommend'] = recommend_data
          return generete_response(statusCode, 'sukses', data_info)
          
    else:
      return generete_response(statusCode, 'gagal', [])
  except Exception as e:
    import traceback
    traceback.print_exc()
    return generete_response(statusCode, 'error', [])


# episode & url download & watch
def episode(episodeSlug):
  response = requests.get(f'{OTAKUDESU_URI}/episode/{episodeSlug}', headers=headers)
  statusCode = response.status_code
  MP4_links = []
  try:
    if statusCode == 200:
      SOUP = BeautifulSoup(response.text, 'html.parser')
      download_section = SOUP.find('div', {'class' : 'download'})
      if download_section:
        for li in download_section.findAll('li'):
          if 'Mp4' in li.find('strong').text:
            links = []
            quality = li.find('strong').text.strip()
            size = li.find('i').text if li.find('i') else 'Unknown Size'
            
            for a in li.find_all('a'):
              link_text = a.text.strip()
              original_url = a['href']
              if 'ODFiles' in link_text or 'Pdrain' in link_text or 'KFiles' in link_text: # or 'Mega' in link_text:
                resolved_url = resolve_safelink(original_url)
                if 'Pdrain' in link_text:
                  link_resp = requests.get(resolved_url, headers=headers)
                  soup = BeautifulSoup(link_resp.text, 'html.parser')
                  link_video = soup.find('meta', {'property' : 'og:video:url'})['content']
                  links.append({
                    'hostName' : link_text, 
                    'url' : link_video
                  })
                else:
                  if 'KFiles' in link_text:
                    k = Kraken()
                    link_video = k.get_and_print_download_link(resolved_url)
                    links.append({
                      'hostName' : link_text,
                      'url' : link_video
                    })
                  else: 
                    links.append({
                      'hostName' : link_text,
                      'url' : resolved_url
                    })
            MP4_links.append({
              'quality': quality,
              'links': links,
              'size': size
            })
            
            
            
        return generete_response(statusCode, 'sukses', MP4_links)
      else:
        return generete_response(statusCode, 'noMedia', [])
    else:
      return generete_response(statusCode, 'gagal', [])
  except Exception as e:
    import traceback
    traceback.print_exc()
    return generete_response(statusCode, 'error', [])
import requests
from bs4 import BeautifulSoup

def property_genre(genreSlug):
    response = requests.get(f'{OTAKUDESU_URI}/genres/{genreSlug}', headers={'User-Agent': 'Mozilla/5.0'})
    statusCode = response.status_code
    animeDATA = []
    
    try:
        if statusCode == 200:
            SOUP = BeautifulSoup(response.text, 'html.parser')
            venkonten = SOUP.find('div', id='venkonten')
            
            # Debugging step: Print the content of venkonten or save it to a file
            if venkonten is None:
                print("Element 'venkonten' not found in the page.")
                with open("page_content.html", "w", encoding='utf-8') as file:
                    file.write(SOUP.prettify())
                return generete_response(statusCode, 'gagal', animeDATA)
            
            for list in venkonten.find_all('div', class_='col-anime'):
                animeName = list.find('div', {'class' : 'col-anime-title'}).getText()
                animeThum = list.find('div', {'class' : 'col-anime-cover'}).find('img')['src']
                animeEpisode = list.find('div', {'class' : 'col-anime-eps'}).getText()
                animeRating = list.find('div', {'class' : 'col-anime-rating'}).getText()
                animeSlug = list.find('div', {'class' : 'col-anime-title'}).find('a')['href'].replace(f'https://otakudesu.cloud/anime/', '')
                
                data = {
                    'animeName' : animeName,
                    'animeThum' : animeThum,
                    'animeEpisode' : animeEpisode,
                    'animeRating' : animeRating,
                    'animeSlug' : animeSlug
                }
                animeDATA.append(data)
            
            return generete_response(statusCode, 'sukses', animeDATA)
        else:
            return generete_response(statusCode, 'gagal', animeDATA)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return generete_response(statusCode, 'error', animeDATA)
  