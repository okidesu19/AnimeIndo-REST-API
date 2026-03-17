import asyncio
from typing import Dict
from fastapi import HTTPException, Query

# Re-export class for backward compatibility
from . import (
    AnimeView, Genres, Schedule, Search, PropertyGenre, AnimeDetail,
    streamingUrl, streamingUrlPlaywright
)
from Config.schemas import ViewType, OrderBy, Day, RequestMethod

# Create instances for backward compatibility
_anime_view = AnimeView()
_genres = Genres()
_schedule = Schedule()
_search = Search()
_property_genre = PropertyGenre()
_anime_detail = AnimeDetail()

async def get_genres(request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _genres.genresPlaywright()
    return _genres.genresRequest()

async def get_anime_view(view: ViewType, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _anime_view.animeViewPlaywright(view, order_by, page)
    return _anime_view.animeViewRequest(view, order_by, page)

async def get_schedule(day: Day, page: int = 1, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _schedule.schedulePlaywright(day, page)
    return _schedule.scheduleRequest(day, page)

async def get_search(query: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _search.searchPlaywright(query, order_by, page)
    return _search.searchRequest(query, order_by, page)

async def get_property_genre(genre: str, order_by: OrderBy = OrderBy.LATEST, page: int = 1, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _property_genre.propertyGenrePlaywright(genre, order_by, page)
    return _property_genre.propertyGenreRequest(genre, order_by, page)

async def get_anime_detail(animeId: str, animeSlug: str, page: int = 1, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await _anime_detail.animeDetailPlaywright(animeId, animeSlug, page)
    return _anime_detail.animeDetailRequest(animeId, animeSlug, page)

async def get_streaming_url(animeId: str, animeSlug: str, episodeId: str, request_method: RequestMethod = RequestMethod.REQUESTS) -> Dict:
    if request_method == RequestMethod.PLAYWRIGHT:
        return await streamingUrlPlaywright(animeId, animeSlug, episodeId)
    return streamingUrl(animeId, animeSlug, episodeId)

__all__ = [
    'get_genres', 'get_anime_view', 'get_schedule', 'get_search',
    'get_property_genre', 'get_anime_detail', 'get_streaming_url',
    # Legacy exports
    'AnimeView', 'Genres', 'Schedule', 'Search', 'PropertyGenre', 
    'AnimeDetail', 'streamingUrl', 'streamingUrlPlaywright'
]
