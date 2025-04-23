import requests
from bs4 import BeautifulSoup
#from Config.config import headers

class HashNotFoundException(Exception):
  def __init__(self, message):
    super().__init__(message)

class LinkPostFailure(Exception):
  def __init__(self, message):
    super().__init__(message)

class Kraken:
    _base_headers = {
      "cache-control": "no-cache",
    }
    
    URL_KEY = "url"
    
    KRAKEN_BASE_URL = "https://krakenfiles.com"
    
    def __init__(self, session: requests.Session = requests.session()):
      self.session = session
      
    def get_download_link(self, page_link: str) -> str:
      page_resp = self.session.get(page_link)
      soup = BeautifulSoup(page_resp.text, "lxml")
        
      # Parse token
      token = soup.find("input", id="dl-token")["value"]
        
      # Attempt to find hash
      hashes = [
        item["data-file-hash"]
        for item in soup.find_all("div", attrs={"data-file-hash": True})
      ]
      if len(hashes) < 1:
        raise HashNotFoundException(f"Hash not found for page_link: {page_link}")
      
      dl_hash = hashes[0]
        
      payload = {
        'token': token,
      }
        
      headers = {
        **self._base_headers,
        "hash": dl_hash,
      }
        
      dl_link_resp = self.session.post(
        f"{self.KRAKEN_BASE_URL}/download/{dl_hash}", data=payload, headers=headers
      )
      dl_link_json = dl_link_resp.json()
        
      if self.URL_KEY in dl_link_json:
        return dl_link_json[self.URL_KEY]
      else:
        raise LinkPostFailure(
          f"Failed to acquire download URL from kraken for page_link: {page_link}"
        )
    
    def get_and_print_download_link(self, page_link: str):
      dl_link = self.get_download_link(page_link)
      return dl_link
