# Kuramanime Parser Package
from .animeView import AnimeView
from .genres import Genres
from .schedule import Schedule
from .search import Search
from .propertyGenre import PropertyGenre
from .animeDetail import AnimeDetail
from .streamingUrl import streamingUrl, streamingUrlPlaywright
from ._extract_streaming_data import _extract_streaming_data

# Create instances for backward compatibility
_anime_view = AnimeView()
_genres = Genres()
_schedule = Schedule()
_search = Search()
_property_genre = PropertyGenre()
_anime_detail = AnimeDetail()

# Export functions for backward compatibility
animeView = _anime_view.animeViewRequest
animeViewPlaywright = _anime_view.animeViewPlaywright
genres = _genres.genresRequest
genresPlaywright = _genres.genresPlaywright
schedule = _schedule.scheduleRequest
schedulePlaywright = _schedule.schedulePlaywright
search = _search.searchRequest
searchPlaywright = _search.searchPlaywright
propertyGenre = _property_genre.propertyGenreRequest
propertyGenrePlaywright = _property_genre.propertyGenrePlaywright
animeDetail = _anime_detail.animeDetailRequest
animeDetailPlaywright = _anime_detail.animeDetailPlaywright

__all__ = [
    'animeView',
    'animeViewPlaywright',
    'genres',
    'genresPlaywright',
    'schedule',
    'schedulePlaywright',
    'search',
    'searchPlaywright',
    'propertyGenre',
    'propertyGenrePlaywright',
    'animeDetail',
    'animeDetailPlaywright',
    'streamingUrl',
    'streamingUrlPlaywright',
    '_extract_streaming_data',
    # Classes
    'AnimeView',
    'Genres',
    'Schedule',
    'Search',
    'PropertyGenre',
    'AnimeDetail',
]
