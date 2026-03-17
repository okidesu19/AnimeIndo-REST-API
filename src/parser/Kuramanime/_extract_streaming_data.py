import logging
from bs4 import BeautifulSoup
from Config.schemas import StreamingQuality, StreamingResponse
from typing import List

# Setup logging
logger = logging.getLogger(__name__)


def _extract_streaming_data(soup: BeautifulSoup, url: str) -> List:
    """Helper function to extract streaming data from BeautifulSoup object with multiple fallbacks."""
    streaming_data = []
    
    # Try multiple selector approaches to find video sources
    
    # Approach 1: Standard video player with source tags
    video_player_div = soup.find('div', {'id': 'animeVideoPlayer'})
    if video_player_div:
        video_player = video_player_div.find('video', {'id': 'player'})
        if video_player:
            source_tags = video_player.find_all('source')
            for tag in source_tags:
                if tag.has_attr('src'):
                    streaming_data.append(
                        StreamingQuality(
                            quality=tag.get('size', 'unknown'),
                            url=tag['src'],
                            type=tag.get('type', 'video/mp4')
                        ).dict()
                    )
    
    # Approach 2: Look for iframe with video src
    if not streaming_data:
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if src and ('v8' in src or 'anime' in src or 'video' in src.lower()):
                streaming_data.append(
                    StreamingQuality(
                        quality="Unknown",
                        url=src,
                        type="video/mp4"
                    ).dict()
                )
                break
    
    # Approach 3: Look for data-src or any src attribute in video-related tags
    if not streaming_data:
        video_tags = soup.find_all(['video', 'source'])
        for tag in video_tags:
            src = tag.get('src') or tag.get('data-src')
            if src:
                streaming_data.append(
                    StreamingQuality(
                        quality=tag.get('quality', 'Unknown'),
                        url=src,
                        type=tag.get('type', 'video/mp4')
                    ).dict()
                )
    
    # Approach 4: Look for server list and extract URLs
    server_list = soup.find('ul', {'id': 'serverList'})
    if server_list and not streaming_data:
        for server in server_list.find_all('li'):
            server_name = server.get('data-name', 'Unknown')
            server_url = server.get('data-url') or server.find('a', href=True)
            if server_url:
                streaming_data.append(
                    StreamingResponse(
                        server=server_name,
                        videos=[StreamingQuality(
                            quality="HD",
                            url=server_url if isinstance(server_url, str) else server_url.get('href'),
                            type="video/mp4"
                        ).dict()]
                    ).dict()
                )
    
    # Log what we found for debugging
    logger.info(f"_extract_streaming_data found {len(streaming_data)} sources from {url}")
    if not streaming_data:
        # Log first 500 chars of HTML for debugging
        html_snippet = str(soup)[:500]
        logger.warning(f"No streaming data found. HTML snippet: {html_snippet}")
    
    return streaming_data
