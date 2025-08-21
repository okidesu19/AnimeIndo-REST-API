import requests
from fastapi.responses import JSONResponse
from typing import Union, Dict, List
import random
OTAKUDESU_URI = 'https://otakudesu.cloud'
KURAMANIME_URI = 'https://v8.kuramanime.tel'

#headers
headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

cookies = {
  "show_country": "JP", 
  "show_genre" : "only_not_hentai"
}


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

headers2 = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
}


def headersJson(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        #"Accept": "text/html, */*,q=0.01",  # Gabungkan semua tipe yang diterima
        #"Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        #"Referer": url,  # Opsional, sesuaikan dengan kebutuhan
        "Accept-Encoding": "gzip, deflate, br",
        #"Sec-Ch-Ua": '"Not A(Brand";v="8", "Chromium";v="132"',  # Perbaiki tanda "
        #"Sec-Ch-Ua-Mobile": "?1",
        #"Sec-Ch-Ua-Platform": '"Android"',  # Perbaiki tanda "
        #"Sec-Fetch-Dest": "empty",  # Ganti dengan "empty" atau "document"
        #"Sec-Fetch-Mode": "cors",
        #"Sec-Fetch-Site": "same-origin",
        #"X-Csrf-Token": "duG6dtaCMEGyQu4zWyUmOLUnI8x3zSjj3E54QY9w",
        
    }
    return headers

def responseRq(url):
  response = requests.get(url, cookies=cookies)
  #response = requests.get(url, proxies=proxies, verify=False)
  return response

# generete_response
def generate_response(status_code: int, message: str, data: Union[Dict, List]):
  response_data = {
    "status": status_code,
    "message": message,
    "data": data
  }
  return response_data


def resolve_safelink(safelink_url):
  # Mengirim permintaan ke safelink untuk mendapatkan URL asli
  response = requests.get(safelink_url, allow_redirects=False)
  if 'Location' in response.headers:
    return response.headers['Location']
  else:
    return safelink_url  # Jika tidak ada redirect, kembalikan URL asli


