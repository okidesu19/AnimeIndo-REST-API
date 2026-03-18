import re
import logging
import asyncio
import random
import os
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import KURAMANIME_URI, responseRq, generate_response
from Config.schemas import ScheduleResponse, PaginatedResponse, Day
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)

# Enhanced User Agents for Playwright
PLAYWRIGHT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Stealth script
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
window.chrome = { runtime: {} };
"""


def get_proxy_config() -> dict:
    """Get proxy configuration from environment variable"""
    proxy_url = os.getenv('PROXY_URL', '')
    
    if not proxy_url:
        return {'enabled': False}
    
    try:
        proxy_parts = proxy_url.replace('http://', '').replace('https://', '').split('@')
        
        if len(proxy_parts) == 2:
            credentials, server = proxy_parts
            username, password = credentials.split(':')
            proxy_config = {
                'enabled': True,
                'server': f'http://{server}',
                'username': username,
                'password': password
            }
        else:
            proxy_config = {
                'enabled': True,
                'server': f'http://{proxy_parts[0]}',
                'username': None,
                'password': None
            }
        
        logger.info(f"Proxy enabled: {proxy_config['server']}")
        return proxy_config
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return {'enabled': False}


class Schedule:
    """Class to handle schedule operations using both requests and Playwright."""

    def scheduleRequest(self, day: Day, page: int = 1) -> PaginatedResponse:
        """Get anime schedule by day using requests."""
        url = f'{KURAMANIME_URI}/schedule?scheduled_day={day}&page={page}'
        anime_data = []
        
        try:
            response = responseRq(url)
            
            if response.status_code == 403:
                logger.error(f"403 Forbidden accessing schedule endpoint: {url}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to schedule data. The source may be blocking requests from your server. Day: {day}, Page: {page}"
                )
            elif response.status_code != 200:
                logger.error(f"Schedule request failed with status {response.status_code}: {url}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch schedule data for {day} (page {page}). Status: {response.status_code}"
                )
            
            if not response.text or len(response.text.strip()) < 100:
                logger.warning(f"Schedule response appears empty or too short: {len(response.text)} chars")
                raise HTTPException(
                    status_code=502,
                    detail=f"Received invalid response from schedule endpoint. The source may be temporarily unavailable."
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in schedule function: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable. Unable to fetch schedule data for {day}: {str(e)}"
            )
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            max_page = 1
            
            nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
            if nav:
                page_links = nav.find_all('a', href=True)
                for link in page_links:
                    href = link['href']
                    if 'page=' in href:
                        page_number = int(href.split('page=')[-1])
                        if page_number > max_page:
                            max_page = page_number
            
            for item in soup.select('.filter__gallery > a'):
                anime_url = item['href']
                match = re.search(r'anime/(\d+)/(.+)', anime_url)
                if match:
                    anime_id = match.group(1)
                    anime_name = item.select_one('.sidebar-title-h5')
                    anime_episode = item.select_one(f'.actual-schedule-ep-{anime_id}')
                    animeEpisode = anime_episode.text.strip() if anime_episode else 'N/A'
                    matchEpisode = re.search(r'Ep\s*(\d+)', animeEpisode)
                    episode = f"Ep {matchEpisode.group(1)}" if matchEpisode else 'N/A'
                    anime_thumb = item.select_one('.set-bg')
                    anime_schedule = item.select_one('.view span')
                    animeSchedule = anime_schedule.text.strip() if anime_schedule else 'N/A'
                    matchTime = re.search(r'\((\d{2}:\d{2} WIB)\)', animeSchedule)
                    time = matchTime.group(1) if matchTime else animeSchedule
                    
                    anime = ScheduleResponse(
                        animeId=anime_id,
                        animeSlug=match.group(2),
                        animeName=anime_name.text.strip() if anime_name else 'N/A',
                        animeEpisode=episode,
                        animeThum=anime_thumb['data-setbg'] if anime_thumb else 'N/A',
                        animeSchedule=time
                    )
                    anime_data.append(anime.dict())
                    
            return PaginatedResponse(
                status=200,
                message="success",
                data=anime_data,
                pagination={
                    "page": page,
                    "maxPage": max_page,
                    "day": day
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=str(e)
            )

    async def schedulePlaywright(self, day: Day, page: int = 1) -> PaginatedResponse:
        """Get anime schedule by day using Playwright with proxy support."""
        url = f'{KURAMANIME_URI}/schedule?scheduled_day={day}&page={page}'
        
        logger.info(f"Fetching schedule using Playwright: {url}")
        
        proxy_config = get_proxy_config()
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    logger.info(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
                
                async with async_playwright() as p:
                    launch_args = [
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--window-size=1920,1080',
                    ]
                    
                    launch_options = {'headless': True, 'args': launch_args}
                    
                    if proxy_config.get('enabled'):
                        proxy = {'server': proxy_config['server']}
                        if proxy_config.get('username') and proxy_config.get('password'):
                            proxy['username'] = proxy_config['username']
                            proxy['password'] = proxy_config['password']
                        launch_options['proxy'] = proxy
                    
                    browser = await p.chromium.launch(**launch_options)
                    
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent=random.choice(PLAYWRIGHT_USER_AGENTS),
                        locale='id-ID',
                        timezone_id='Asia/Jakarta',
                        extra_http_headers={
                            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Referer': 'https://www.google.com/',
                        }
                    )
                    
                    page_obj = await context.new_page()
                    await page_obj.add_init_script(STEALTH_SCRIPT)
                    
                    await page_obj.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    html = await page_obj.content()
                    await browser.close()
                    
                soup = BeautifulSoup(html, 'html.parser')
                anime_data = []
                max_page = 1
                
                nav = soup.find('nav', {'aria-label': 'Pagination Navigation'})
                if nav:
                    page_links = nav.find_all('a', href=True)
                    for link in page_links:
                        href = link['href']
                        if 'page=' in href:
                            page_number = int(href.split('page=')[-1])
                            max_page = max(max_page, page_number)
                
                for item in soup.select('.filter__gallery > a'):
                    anime_url = item['href']
                    match = re.search(r'anime/(\d+)/(.+)', anime_url)
                    if match:
                        anime_id = match.group(1)
                        anime_name = item.select_one('.sidebar-title-h5')
                        anime_episode = item.select_one(f'.actual-schedule-ep-{anime_id}')
                        animeEpisode = anime_episode.text.strip() if anime_episode else 'N/A'
                        matchEpisode = re.search(r'Ep\s*(\d+)', animeEpisode)
                        episode = f"Ep {matchEpisode.group(1)}" if matchEpisode else 'N/A'
                        anime_thumb = item.select_one('.set-bg')
                        anime_schedule = item.select_one('.view span')
                        animeSchedule = anime_schedule.text.strip() if anime_schedule else 'N/A'
                        matchTime = re.search(r'\((\d{2}:\d{2} WIB)\)', animeSchedule)
                        time = matchTime.group(1) if matchTime else animeSchedule
                        
                        anime = ScheduleResponse(
                            animeId=anime_id,
                            animeSlug=match.group(2),
                            animeName=anime_name.text.strip() if anime_name else 'N/A',
                            animeEpisode=episode,
                            animeThum=anime_thumb['data-setbg'] if anime_thumb else 'N/A',
                            animeSchedule=time
                        )
                        anime_data.append(anime.dict())
                
                fetch_method = "Playwright"
                if proxy_config.get('enabled'):
                    fetch_method = "Playwright + Proxy"
                
                return PaginatedResponse(
                    status=200,
                    message='success',
                    data=anime_data,
                    pagination={
                        'day': day,
                        'page': page,
                        'maxPage': max_page,
                        'fetchMethod': fetch_method,
                        'proxyEnabled': proxy_config.get('enabled', False)
                    }
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                continue
        
        raise HTTPException(
            status_code=504,
            detail=f"Playwright timeout after {max_retries} attempts: {last_error}"
        )
