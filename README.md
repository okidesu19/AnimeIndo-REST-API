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