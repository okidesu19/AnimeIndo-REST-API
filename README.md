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
2. `SSH_HOST` + `SSH_USER` + `SSH_PASSWORD` (SSH tunnel sebagai proxy fallback)
3. `BRIGHTDATA_PROXY`
4. `SCRAPERAPI_KEY` (ScraperAPI)
5. `SCRAPINGBEE_KEY` (ScrapingBee)
6. Playwright (fallback terakhir, development only)

**SSH Tunnel Configuration:**

Jika Anda memiliki akun SSH server, Anda bisa menggunakannya sebagai proxy via SSH tunnel:

```bash
export SSH_HOST="your.ssh.server"
export SSH_USER="username"
export SSH_PASSWORD="password"
# atau gunakan SSH key (ubah code jika diperlukan)
```
Prioritas pemakaian pada server:

1. `PROXY_URL` / explicit proxy vars (paling prioritas)
2. `WEBSHARE_API_KEY` + `WEBSHARE_API_PASSWORD` (WebShare free proxy)
3. `SSH_HOST` + `SSH_USER` + `SSH_PASSWORD` (SSH tunnel - LionSSH, FastSSH, dll)
4. `BRIGHTDATA_PROXY`
5. `SCRAPERAPI_KEY` (ScraperAPI)
6. `SCRAPINGBEE_KEY` (ScrapingBee)
7. Playwright (fallback terakhir, development only)

### **Free SSH Services Setup:**

#### **1. LionSSH (lionssh.com)**
- Daftar gratis di https://lionssh.com
- Dapatkan akun SSH: host, username, password
- Set di `.env`:
```bash
SSH_HOST=your-lionssh-host.com
SSH_USER=your_username
SSH_PASSWORD=your_password
```

#### **2. FastSSH (fastssh.com)**
- Daftar gratis di https://fastssh.com
- Dapatkan akun SSH: host, username, password
- Set di `.env`:
```bash
SSH_HOST=your-fastssh-host.com
SSH_USER=your_username
SSH_PASSWORD=your_password
```

### **Free Proxy Service Setup:**

#### **3. WebShare (webshare.io)**
- Gratis 10 proxy per bulan di https://www.webshare.io/free-proxy
- Daftar, ambil API key dan password dari dashboard
- Set di `.env`:
```bash
WEBSHARE_API_KEY=your_api_key
WEBSHARE_API_PASSWORD=your_api_password
```

**Contoh `.env` lengkap dengan semua opsi:**

```
# Opsi 1: Direct proxy (jika punya)
PROXY_URL=http://user:pass@proxy-host:port

# Opsi 2: WebShare free proxy (gratis tapi limited)
WEBSHARE_API_KEY=your_webshare_api_key
WEBSHARE_API_PASSWORD=your_webshare_password

# Opsi 3: SSH tunnel (LionSSH atau FastSSH gratis)
SSH_HOST=your-ssh-host.com
SSH_USER=your_ssh_username
SSH_PASSWORD=your_ssh_password

# Opsi 4: BrightData proxy
BRIGHTDATA_PROXY=http://username:password@brd.proxy.example:port

# Opsi 5: ScraperAPI
SCRAPERAPI_KEY=your_scraperapi_key

# Opsi 6: ScrapingBee (Anda sudah punya ini)
SCRAPINGBEE_KEY=29QJ0HGZXCPTTWDLFW2PNRVH6TUUIH8TI048LGAQ659OEIXQ70O7KG7YYK2A3VNP13PNMOEKJT7VJ2M0
```

**Rekomendasi:**
- **Terbaik untuk free tier:** WebShare (simple, cepat setup, 10 proxy gratis/bulan)
- **Alternatif terbaik:** SSH tunnel dari LionSSH/FastSSH (unlimited, reliable)
- **Production:** Gunakan SCRAPERAPI_KEY atau SCRAPINGBEE_KEY (tested, reliable)

Contoh file helper sudah disediakan di `scripts/setup_scraper_env.sh` untuk panduan cepat.

Contoh `.env`:

```
SSH_HOST=my-server.com
SSH_USER=ubuntu
SSH_PASSWORD=my_secure_password
```

**atau Lengkap dengan semua opsi:**

```
PROXY_URL=http://user:pass@proxy-host:port
BRIGHTDATA_PROXY=http://username:password@brd.proxy.example:port
SCRAPERAPI_KEY=your_scraperapi_key
SCRAPINGBEE_KEY=your_scrapingbee_key
SSH_HOST=your.ssh.server
SSH_USER=username
SSH_PASSWORD=password
```

Contoh file helper sudah disediakan di `scripts/setup_scraper_env.sh` untuk panduan cepat.

Contoh pengaturan di Vercel/Railway: tambahkan `PROXY_URL` atau `SCRAPERAPI_KEY` di Environment Variables pada project settings lalu redeploy.

Quick local test:

```bash
export SCRAPERAPI_KEY="your_key_here"
uvicorn main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/krm/genres/
```

Log di server sekarang mencetak lebih banyak informasi saat terjadi `403`, sehingga Anda bisa melihat potongan body/headers untuk debugging.