import requests

payload = { 'api_key': 'c04932736fc112f09e3a9ed32ec7b2f2', 'url': 'https://v8.kuramanime.tel', 'output_format': 'json', 'autoparse': 'true', 'device_type': 'desktop' }
r = requests.get('https://api.scraperapi.com/', params=payload)
print(r.text)
