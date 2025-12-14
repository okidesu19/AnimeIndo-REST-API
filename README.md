# 📺 ANIME INDO API

A modern REST API for accessing anime data, built with FastAPI and Playwright.
[ANIME INDO REST API](https://animeindo-rest-api.up.railway.app)
## 🌟 Features

- 🚀 Fast and reliable anime data scraping
- 🔍 Search anime by title, genre, or schedule
- 📺 Get streaming links for episodes
- 📅 View anime schedules by day
- 🛠️ Built with FastAPI and Playwright
- 📦 Fully containerized with Docker

## 📦 Installation

### Prerequisites
- Python 3.10+
- Playwright browsers installed
- Docker (optional)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/okidesu19/AnimeIndo-REST-API
cd AnimeIndo-REST-API
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
playwright install-deps
```

3. Run the API:
```bash
fastapi dev main.py
```

## 🚀 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/krm/view/{view}` | GET | Get anime by view type (ongoing/finished) |
| `/api/krm/genres/` | GET | Get all available genres |
| `/api/krm/schedule/{day}` | GET | Get anime schedule by day |
| `/api/krm/search/` | GET | Search anime by query |
| `/api/krm/genre/{genre}` | GET | Get anime by genre |
| `/api/krm/anime/{animeId}/{animeSlug}/` | GET | Get anime details |
| `/api/krm/anime/{animeId}/{animeSlug}/episode/{episodeId}` | GET | Get streaming links |

## 📚 Documentation
Interactive API documentation is available at:
- Swagger UI: [`/docs`](https://animeindo-rest-api.up.railway.app/docs)
- ReDoc: [`/redoc`](https://animeindo-rest-api.up.railway.app/redoc)

## 📧 Contact
For questions or support, please contact:
- Jonathan - jonathansigalinggin012@gmail.com
- Project Link: [AnimeIndo-REST-API](https://github.com/okidesu19/AnimeIndo-REST-API)

---

<p align="center">
  Made with ❤️ and Python
</p>

## Proxy / Scraper fallback (Deployment)

Jika saat deploy (Vercel / Railway) Anda mendapat `403 Forbidden`, kemungkinan besar IP server cloud diblokir oleh sumber. Ada dua opsi cepat:

- Gunakan proxy (residential/rotating). Set environment variable `PROXY_URL` pada platform deploy Anda. Contoh nilai:

```
http://user:pass@host:port
```

- Jika Anda tidak bisa pakai proxy, gunakan layanan scraping seperti ScraperAPI. Set environment variable `SCRAPERAPI_KEY` dan sistem akan otomatis merutekan request melalui ScraperAPI.

Lanjutan: dukungan provider lain

- `BRIGHTDATA_PROXY`: jika Anda memakai BrightData (Luminati) atau proxy yang perlu credentials, setkan proxy URL secara eksplisit. Contoh:

```
export BRIGHTDATA_PROXY="http://username:password@proxy-host:port"
```

- `SCRAPINGBEE_KEY`: jika Anda menggunakan ScrapingBee, set:

```
export SCRAPINGBEE_KEY="your_scrapingbee_key"
```

Prioritas pemakaian pada server:

1. `PROXY_URL` / explicit proxy vars (paling prioritas)
2. `BRIGHTDATA_PROXY`
3. `SCRAPERAPI_KEY` (ScraperAPI)
4. `SCRAPINGBEE_KEY` (ScrapingBee)

Contoh file helper sudah disediakan di `scripts/setup_scraper_env.sh` untuk panduan cepat.

Contoh pengaturan di Vercel/Railway: tambahkan `PROXY_URL` atau `SCRAPERAPI_KEY` di Environment Variables pada project settings lalu redeploy.

Quick local test:

```bash
export SCRAPERAPI_KEY="your_key_here"
uvicorn main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/krm/genres/
```

Log di server sekarang mencetak lebih banyak informasi saat terjadi `403`, sehingga Anda bisa melihat potongan body/headers untuk debugging.