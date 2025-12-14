import requests

payload = { 'api_key': 'eff2f459c8daa269c85aa5623dc2ea6e', 'url': 'https://v8.kuramanime.tel/', 'device_type': 'desktop', 'country_code': 'id', 'keep_headers': 'true' }
r = requests.get('https://api.scraperapi.com/', params=payload)
print(r.text)
