import asyncio
from typing import Dict
from fastapi import HTTPException, Query

# Re-export original functions for backward compatibility
from . import (
    animeView, genres, schedule, search, propertyGenre, animeDetail,
    streamingUrl, streamingUrlPlaywright, genres_playwright, animeView_playwright,
    schedule_playwright, search_playwright, propertyGenre_playwright, animeDetail_playwright
)

async def get_genres(request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await genres_playwright()
    return genres()

from Config.schemas import ViewType, OrderBy, Day

async def get_anime_view(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        from .animeView_playwright import animeView_playwright
        return await animeView_playwright(view, order_by, page)
    return animeView(view, order_by, page)

async def get_schedule(day: Day, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        from .schedule_playwright import schedule_playwright
        return await schedule_playwright(day, page)
    return schedule(day, page)

async def get_search(query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        from .search_playwright import search_playwright
        return await search_playwright(query, order_by, page)
    return search(query, order_by, page)

async def get_property_genre(genre: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        from .propertyGenre_playwright import propertyGenre_playwright
        return await propertyGenre_playwright(genre, order_by, page)
    return propertyGenre(genre, order_by, page)

async def get_anime_detail(animeId: str, animeSlug: str, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        from .animeDetail_playwright import animeDetail_playwright
        return await animeDetail_playwright(animeId, animeSlug, page)
    return animeDetail(animeId, animeSlug, page)

async def get_streaming_url(animeId: str, animeSlug: str, episodeId: str, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await streamingUrlPlaywright(animeId, animeSlug, episodeId)
    return streamingUrl(animeId, animeSlug, episodeId)

__all__ = [
    'get_genres', 'get_anime_view', 'get_schedule', 'get_search',
    'get_property_genre', 'get_anime_detail', 'get_streaming_url',
    # Legacy exports
    'genres', 'animeView', 'schedule', 'search', 'propertyGenre', 
    'animeDetail', 'streamingUrl', 'streamingUrlPlaywright'
]

