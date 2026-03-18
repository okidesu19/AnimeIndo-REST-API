import re
import logging
import asyncio
import random
from bs4 import BeautifulSoup
from fastapi import HTTPException
from Config.config import (
    KURAMANIME_URI, 
    responseRq,
    get_proxy_config,
    get_browser_launch_args,
    get_context_options,
    PLAYWRIGHT_STEALTH_SCRIPT
)
from Config.schemas import (
    AnimeViewResponse, PaginatedResponse, OrderBy, ViewType
)
from playwright.async_api import async_playwright
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)


class AnimeView:
    """Class to handle anime view operations using both requests and Playwright."""

    def animeViewRequest(self, view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
        """Get anime list by view type (ongoing/finished) using requests."""
        anime_data = []
        
        view_mapping = {
            ViewType.ONGOING: "Ongoing",
            ViewType.FINISHED: "Completed"
        }
        VIEW = view_mapping.get(view, "Ongoing")
        
        url = f'{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page={page}'
        
        try:
            response = responseRq(url)
            if response.status_code == 403:
                logger.error(f"403 Forbidden accessing anime view endpoint: {url}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to anime view data. The source may be blocking requests from your server. View: {view}, Order: {order_by}, Page: {page}"
                )
            elif response.status_code != 200:
                logger.error(f"Anime view request failed with status {response.status_code}: {url}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch anime view data for {view} (page {page}). Status: {response.status_code}"
                )
            
            if not response.text or len(response.text.strip()) < 100:
                logger.warning(f"Anime view response appears empty or too short: {len(response.text)} chars")
                raise HTTPException(
                    status_code=502,
                    detail=f"Received invalid response from anime view endpoint. The source may be temporarily unavailable."
                )
                        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in animeView function: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable. Unable to fetch anime view data for {view}: {str(e)}"
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
                    anime_view = item.select_one('.view')
                    anime_thum = item.select_one('.set-bg')
                    anime_name = item.select_one('.sidebar-title-h5')
                    
                    anime_episode = None
                    anime_star = None
                    
                    if view == ViewType.ONGOING:
                        episode_star_tag = item.select_one(f'.actual-anime-{anime_id}-ongoing') or item.select_one('.ep span')
                        anime_episode = episode_star_tag.text.strip() if episode_star_tag else None
                    elif view == ViewType.FINISHED:
                        star_tag = item.select_one(f'.actual-anime-{anime_id}')
                        anime_star = star_tag.text.strip() if star_tag else None
                    
                    anime = AnimeViewResponse(
                        animeId=anime_id,
                        animeSlug=match.group(2),
                        animeName=anime_name.text.strip() if anime_name else 'N/A',
                        animeThum=anime_thum['data-setbg'] if anime_thum else None,
                        animeView=anime_view.text.strip() if anime_view else 'HD',
                        animeStar=anime_star,
                        animeEpisode=anime_episode
                    )
                    anime_data.append(anime.dict())
            
            return PaginatedResponse(
                status=200,
                message="success",
                data=anime_data,
                pagination={
                    "view": VIEW,
                    "page": page,
                    "maxPage": max_page
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    async def animeViewPlaywright(self, view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1) -> PaginatedResponse:
        """Get anime list by view type using Playwright with proxy support."""
        anime_data = []
        
        view_mapping = {
            ViewType.ONGOING: "Ongoing",
            ViewType.FINISHED: "Completed"
        }
        VIEW = view_mapping.get(view, "Ongoing")
        
        url = f'{KURAMANIME_URI}/quick/{view}?order_by={order_by}&page={page}'
        
        logger.info(f"Fetching animeView using Playwright: {url} (view={view}, order={order_by}, page={page})")
        
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
                    launch_args = get_browser_launch_args()
                    launch_options = {'headless': True, 'args': launch_args}
                    
                    if proxy_config.get('enabled'):
                        proxy = {'server': proxy_config['server']}
                        if proxy_config.get('username') and proxy_config.get('password'):
                            proxy['username'] = proxy_config['username']
                            proxy['password'] = proxy_config['password']
                        launch_options['proxy'] = proxy
                        logger.info(f"Using proxy: {proxy_config['server']}")
                    
                    browser = await p.chromium.launch(**launch_options)
                    
                    context_options = get_context_options()
                    context = await browser.new_context(**context_options)
                    
                    page_obj = await context.new_page()
                    await page_obj.add_init_script(PLAYWRIGHT_STEALTH_SCRIPT)
                    
                    await page_obj.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    html = await page_obj.content()
                    await browser.close()
                
                if not html or len(html.strip()) < 100:
                    raise HTTPException(status_code=502, detail="Invalid response from source")
                
                break
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Playwright fetch failed for animeView: {str(e)}")
                continue
        
        if last_error and not html:
            raise HTTPException(status_code=503, detail=str(last_error))
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
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
                    anime_view = item.select_one('.view')
                    anime_thum = item.select_one('.set-bg')
                    anime_name = item.select_one('.sidebar-title-h5')
                    
                    anime_episode = None
                    anime_star = None
                    
                    if view == ViewType.ONGOING:
                        episode_star_tag = item.select_one(f'.actual-anime-{anime_id}-ongoing') or item.select_one('.ep span')
                        anime_episode = episode_star_tag.text.strip() if episode_star_tag else None
                    elif view == ViewType.FINISHED:
                        star_tag = item.select_one(f'.actual-anime-{anime_id}')
                        anime_star = star_tag.text.strip() if star_tag else None
                    
                    anime = AnimeViewResponse(
                        animeId=anime_id,
                        animeSlug=match.group(2),
                        animeName=anime_name.text.strip() if anime_name else 'N/A',
                        animeThum=anime_thum['data-setbg'] if anime_thum else None,
                        animeView=anime_view.text.strip() if anime_view else 'HD',
                        animeStar=anime_star,
                        animeEpisode=anime_episode
                    )
                    anime_data.append(anime.dict())
            
            fetch_method = "Playwright"
            if proxy_config.get('enabled'):
                fetch_method = "Playwright + Proxy"
            
            return PaginatedResponse(
                status=200,
                message="success",
                data=anime_data,
                pagination={
                    "view": VIEW,
                    "page": page,
                    "maxPage": max_page,
                    "fetchMethod": fetch_method,
                    "proxyEnabled": proxy_config.get('enabled', False)
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
