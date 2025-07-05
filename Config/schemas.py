from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum
from typing import Optional, List, Dict, Union
from pydantic import BaseModel

class OrderBy(str, Enum):
  ASCENDING = "ascending"
  DESCENDING = "descending"
  OLDEST = "oldest"
  LATEST = "latest"
  POPULAR = "popular"
  MOST_VIEWED = "most_viewed"
  UPDATED = "updated"

class Day(str, Enum):
  ALL = "all"
  RANDOM = "random"
  MONDAY = "monday"
  TUESDAY = "tuesday"
  WEDNESDAY = "wednesday"
  THURSDAY = "thursday"
  FRIDAY = "friday"
  SATURDAY = "saturday"
  SUNDAY = "sunday"

class ViewType(str, Enum):
  ONGOING = "ongoing"
  FINISHED = "finished"

class AnimeBase(BaseModel):
  animeId: str
  animeSlug: str
  animeName: str
  animeThum: Optional[str] = None

class AnimeViewResponse(AnimeBase):
  animeEpisode: Optional[str] = None
  animeView: Optional[str] = None

class GenreResponse(BaseModel):
  genreName: str
  genreSlug: str

class ScheduleResponse(AnimeViewResponse):
  animeSchedule: Optional[str] = None

class SearchResponse(AnimeViewResponse):
  animeStar: Optional[str] = None

class StreamingQuality(BaseModel):
  quality: str
  url: str
  type: str

class StreamingResponse(BaseModel):
  server: str
  videos: List[StreamingQuality]

class Episode(BaseModel):
  episodeId: str
  episodeNumber: str
  episodeTitle: str
  episodeUrl: str

class PaginationDetail(BaseModel):
  hasNextPage: bool
  nextPageUrl: Optional[str] = None
  currentPage: str

class AnimeDetailResponse(AnimeBase):
  animeView: Optional[str] = None
  animeType: Optional[str] = None
  animeTotalEpisodes: Optional[str] = None
  animeStatus: Optional[str] = None
  animeRelease: Optional[str] = None
  animeDuration: Optional[str] = None
  animeCountry: Optional[str] = None
  animeAdaptation: Optional[str] = None
  animeSinopsis: Optional[str] = None
  animeGenres: List[GenreResponse]
  episodes: List[Episode]
  pagination: Optional[PaginationDetail] = None

class PaginatedResponse(BaseModel):
  status: int
  message: str
  data: List[AnimeViewResponse]
  pagination: Dict[str, Optional[int | str]]