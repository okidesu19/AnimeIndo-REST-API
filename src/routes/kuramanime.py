from fastapi import APIRouter, HTTPException, Request, Query
from src.parser.Kuramanime.kuramanime import (
    animeView, genres, schedule, search, 
    propertyGenre, animeDetail, streamingUrl
)
from Config.schemas import OrderBy, Day, ViewType, PaginatedResponse

router = APIRouter(
  prefix="/api/krm", 
  tags=["Anime Indo API"], 
  responses={404: {"description": "Not found"}}
)

@router.get("/view/{view}", response_model=PaginatedResponse)
async def anime_view_route(view: ViewType, order_by: OrderBy = Query(OrderBy.LATEST, description="Sorting order")):
  """Get anime list by view type (ongoing/finished)"""
  return animeView(view.value, order_by.value)

@router.get("/genres/")
async def genres_route():
  """Get list of all available genres"""
  return genres()

@router.get("/schedule/{day}", response_model=PaginatedResponse)
async def schedule_route(
  day: Day,
  page: int = Query(1, gt=0, description="Page number"),
):
  """Get anime schedule by day"""
  return schedule(day.value, page)

@router.get("/search/", response_model=PaginatedResponse)
async def search_route(
  query: str = Query(..., min_length=1, description="Search query"),
  order_by: OrderBy = Query(OrderBy.LATEST, description="Sorting order"),
  page: int = Query(1, gt=0, description="Page number"),
):
  """Search anime by query"""
  return search(query, order_by.value, page)

@router.get("/genre/{genre}", response_model=PaginatedResponse)
async def property_genre_route(
  genre: str,
  order_by: OrderBy = Query(OrderBy.LATEST, description="Sorting order"),
  page: int = Query(1, gt=0, description="Page number"),
):
  """Get anime list by genre"""
  return propertyGenre(genre, order_by.value, page)

@router.get("/anime/{animeId}/{animeSlug}/")
async def detail_route(
  animeId: str,
  animeSlug: str,
  page: str = Query("1", description="Episode page number"),
):
  """Get anime details and episodes"""
  return animeDetail(animeId, animeSlug, page)

@router.get("/anime/{animeId}/{animeSlug}/episode/{episodeId}")
async def streaming_route(
  animeId: str,
  animeSlug: str,
  episodeId: str,
):
  """Get streaming URLs for an episode"""
  return await streamingUrl(animeId, animeSlug, episodeId)



#>---- Order By ----<#
#> A-Z = ascending
#> Z-A = descending
#> Terlama = oldest
#> Terbaru = latest
#> Teratas = popular
#> Terpopuler = most_viewed
#> Terupdate = updated

#>---- SHEDULE ----<#
#> Semua = all
#> Random = random
#> Senin = monday
#> Selasa = tuesday
#> Rabu = wednesday
#> Kamis = thursday
#> Jumat = friday
#> Sabtu = saturday
#> Minggu = sunday

#>---- AnimeView ----<#
#> Sedang Tayang = ongoing
#> Selesai Tayang = finished