from fastapi import FastAPI
from src.routes.kuramanime import router as kuramanime_router
import os
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Startup health check for Playwright if TYPE_GET_STREAMING=PLAYWRIGHT
def check_playwright_availability():
    """Check if Playwright is available when TYPE_GET_STREAMING=PLAYWRIGHT"""
    type_get_streaming = (os.getenv('TYPE_GET_STREAMING') or '').strip().lower()
    if type_get_streaming == 'playwright':
        try:
            import playwright
            logger.info("✓ Playwright is available")
            return True
        except ImportError:
            logger.error("✗ TYPE_GET_STREAMING=PLAYWRIGHT but playwright not installed!")
            logger.error("  Install with: pip install playwright && playwright install chromium")
            return False
    return True

app = FastAPI(
  title="Anime Indo API",
  description="API for scraping anime data from various sources",
  version="1.0.0",
  docs_url="/docs",
  redoc_url="/redoc",
)

# Run startup check
if not check_playwright_availability():
    logger.warning("Starting without Playwright support")

# CORS Middleware
# app.add_middleware(
#   CORSMiddleware,
#   allow_origins=["*"],
#   allow_credentials=False,
#   allow_methods=["*"],
#   allow_headers=["*"],
# )

app.add_middleware(
  CORSMiddleware,
  allow_origins=["https://animeindo-rest-api.up.railway.app"],
  allow_credentials=True,
  allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allow_headers=["Authorization", "Content-Type"],
  expose_headers=["Content-Length", "X-JSON"]
)

# Include routers
app.include_router(kuramanime_router)

@app.get("/", tags=["Root"])
async def root():
  return {
    "message": "Welcome to Anime Indo API",
    "docs": "/docs",
    "redoc": "/redoc"
  }
  
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
