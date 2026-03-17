import logging
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, generate_response, responseRq
from Config.schemas import StreamingQuality, StreamingResponse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List
from ._extract_streaming_data import _extract_streaming_data

# Setup logging
logger = logging.getLogger(__name__)


def streamingUrl(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    """
    Default method to get streaming URL for an episode using requests + BeautifulSoup.
    This is the default/fallback method.
    """
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
     
    logger.info(f"Fetching streaming URL using requests (default): {url}")
    try:
        response = responseRq(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch streaming URL: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch streaming URL. Status: {response.status_code}"
            )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        streaming_data = _extract_streaming_data(soup, url)
        
        fetch_method = "Requests (Default)"
        if streaming_data:
            logger.info(f"✓ Found {len(streaming_data)} sources via requests")
            return generate_response(200, 'success', {
                "streamingSources": streaming_data,
                "episodeInfo": {
                    "animeId": animeId,
                    "animeSlug": animeSlug,
                    "episodeId": episodeId
                },
                "fetchMethod": fetch_method
            })
        return generate_response(404, 'No video sources found', {})
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Requests fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch streaming URL. Error: {str(e)}")


async def streamingUrlPlaywright(animeId: str, animeSlug: str, episodeId: str) -> Dict:
    """
    Method to get streaming URL for an episode using Playwright.
    This uses full browser automation.
    """
    url = f'{KURAMANIME_URI}/anime/{animeId}/{animeSlug}/episode/{episodeId}'
    streaming_data = []
    print(url)
    
    fetch_method = None
    
    logger.info(f"Fetching streaming URL using Playwright: {url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigasi ke URL dengan timeout lebih pendek
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Tunggu elemen video player muncul
            try:
                await page.wait_for_selector('#animeVideoPlayer', timeout=5000)
            except:
                logger.warning("Video player selector not found, proceeding anyway")
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            streaming_data = _extract_streaming_data(soup, url)
            await browser.close()
            
            fetch_method = "Playwright"
            if streaming_data:
                logger.info(f"✓ Found {len(streaming_data)} sources via Playwright")
                return generate_response(200, 'success', {
                    "streamingSources": streaming_data,
                    "episodeInfo": {
                        "animeId": animeId,
                        "animeSlug": animeSlug,
                        "episodeId": episodeId
                    },
                    "fetchMethod": fetch_method
                })
            return generate_response(404, 'No video sources found', {})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'browser' in locals():
            await browser.close()
        logger.error(f"Playwright fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch streaming URL. Error: {str(e)}")
