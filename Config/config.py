import requests
from fastapi.responses import JSONResponse
from typing import Union, Dict, List

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

headers2 = {
    "Date": "Fri, 01 Aug 2025 12:17:31 GMT",
    "Content-Type": "text/html; charset=UTF-8",
    "Transfer-Encoding": "chunked",
    "Connection": "keep-alive",
    "Server": "cloudflare",
    "Nel": "{\"report_to\":\"cf-nel\",\"success_fraction\":0.0,\"max_age\":604800}",
    "Vary": "Accept-Encoding",
    "Cache-Control": "no-cache, private",
    "X-Frame-Options": "SAMEORIGIN",
    "X-Xss-Protection": "1; mode=block",
    "X-Content-Type-Options": "nosniff",
    "Report-To": "{\"group\":\"cf-nel\",\"max_age\":604800,\"endpoints\":[{\"url\":\"https://a.nel.cloudflare.com/report/v4?s=J1jLu616f07ktEGSEuck85rD2JV1GcYTPFDBHRnIn%2FBHlebVth%2BWXE6WuqQlUDiY7XbDxU11nDzrjU220JQWmHETU7zLcqA7Ef8Kk%2FLa5dBA\"}]}",
    "Cf-Cache-Status": "DYNAMIC",
    "Speculation-Rules": "\"/cdn-cgi/speculation\"",
    "Content-Encoding": "gzip",
    "Set-Cookie": "XSRF-TOKEN=eyJpdiI6InhuTGJsVU1pN1hiTURjUFNmUUprZVE9PSIsInZhbHVlIjoidWxPd05zZ1pFdHBTNFdFRGhWZ1JaTFlialNHdVBSMFY4blZ3NjZoSTkzVWlzeXh5RWpUNWx3dXpDUzZVZ1MwU05BK0g3YXZ1cUhQV3cxajFNaGx0SzRaQ0IzUVpNem1lOTNuMy9sQy9FbjZFUmk3UENUYjZHMnhxYTQyRUUxRE0iLCJtYWMiOiIwNDI5MjViYjNjYmY0Mzk3NTRlOTRkMTYyMjdhYWQ5NmVkNWIwZjZmYzY0NWEyYTRmMzU4YzA1ZDg4Zjk0ZWJjIiwidGFnIjoiIn0%3D; SameSite=Lax; Secure; Path=/; Domain=kuramanime.tel; Max-Age=7200; Expires=Fri, 01 Aug 2025 14:17:31 GMT, kuramanime_session=eyJpdiI6IjFWMjcyVVd1NkRwRDVlbzdSbkJweGc9PSIsInZhbHVlIjoiZUtSbnF3ZUM2clpmRlBjUko4U1pxd2FNYVFQNGRkZ29oMk5zZ0ZKb2xJUlBhbTh3dmVJYzMxQjhoaFNmcVpiMldUQnZvNzZSUXZtNy9XNUVNVm5UbDk1aE52VU85dWw0T0VoaW1iUG1YRkN1TU5jei9QSHhQUjhIUFoyemMzVkMiLCJtYWMiOiJkMzgxNzJhNzI5MTgzNjFmN2VkMWFiOTFkNTUzMjYzMzhiOWFkNzZjNGVlZGY5ODlhMjNmNDIzY2E3YzZiMTQwIiwidGFnIjoiIn0%3D; HttpOnly; SameSite=Lax; Path=/; Domain=kuramanime.tel",
    "CF-RAY": "968545db08a091b7-SIN",
    "alt-svc": "h3=\":443\"; ma=86400"
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
  response = requests.get(url, cookies=cookies, headers=headers2)
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


