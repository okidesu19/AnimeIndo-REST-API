import asyncio
from typing import Dict
from fastapi import HTTPException, Query

# Re-export original functions for backward compatibility
from . import (
    animeView, animeViewPlaywright, genres, genresPlaywright, 
    schedule, schedulePlaywright, search, searchPlaywright, 
    propertyGenre, propertyGenrePlaywright, animeDetail, animeDetailPlaywright,
    streamingUrl, streamingUrlPlaywright
)

from Config.schemas import ViewType, OrderBy, Day


async def get_genres(request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await genresPlaywright()
    return genres()


async def get_anime_view(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await animeViewPlaywright(view, order_by, page)
    return animeView(view, order_by, page)


async def get_schedule(day: Day, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await schedulePlaywright(day, page)
    return schedule(day, page)


async def get_search(query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await searchPlaywright(query, order_by, page)
    return search(query, order_by, page)


async def get_property_genre(genre: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await propertyGenrePlaywright(genre, order_by, page)
    return propertyGenre(genre, order_by, page)


async def get_anime_detail(animeId: str, animeSlug: str, page: int = 1, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await animeDetailPlaywright(animeId, animeSlug, page)
    return animeDetail(animeId, animeSlug, page)


async def get_streaming_url(animeId: str, animeSlug: str, episodeId: str, request_method: str = "requests") -> Dict:
    if request_method == "playwright":
        return await streamingUrlPlaywright(animeId, animeSlug, episodeId)
    return streamingUrl(animeId, animeSlug, episodeId)


__all__ = [
    'get_genres', 'get_anime_view', 'get_schedule', 'get_search',
    'get_property_genre', 'get_anime_detail', 'get_streaming_url',
    # Legacy exports
    'genres', 'genresPlaywright', 'animeView', 'animeViewPlaywright',
    'schedule', 'schedulePlaywright', 'search', 'searchPlaywright',
    'propertyGenre', 'propertyGenrePlaywright', 'animeDetail', 'animeDetailPlaywright',
    'streamingUrl', 'streamingUrlPlaywright'
]
