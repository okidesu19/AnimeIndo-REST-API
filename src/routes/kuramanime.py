
from fastapi import APIRouter, HTTPException, Request, Query
from src.parser.Kuramanime.kuramanime import (
    animeView, genres, schedule, search, 
    propertyGenre, animeDetail, streamingUrl
)
from Config.schemas import OrderBy, Day, ViewType, PaginatedResponse
from Config.config import health_check
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
  prefix="/api/krm", 
  tags=["Anime Indo API"], 
  responses={404: {"description": "Not found"}}
)

@router.get("/view/{view}", response_model=PaginatedResponse)
async def anime_view_route(
  view: ViewType, 
  order_by: OrderBy = Query(OrderBy.LATEST, description="Sorting order"), 
  page: int = Query(1, gt=0, description="Page number")
):
  """Get anime list by view type (ongoing/finished)"""
  return animeView(view.value, order_by.value, page)

@router.get("/genres")
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

@router.get("/search", response_model=PaginatedResponse)
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

@router.get("/anime/{animeId}/{animeSlug}")
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

@router.get("/health")
async def health_check_route():
  """Health check endpoint to test connection to source"""
  try:
    result = health_check()
    status_code = 200 if result["status"] == "healthy" else 503
    return {
      "status": status_code,
      "message": "Health check completed",
      "data": result
    }
  except Exception as e:
    logger.error(f"Health check failed: {str(e)}")
    return {
      "status": 503,
      "message": "Health check failed",
      "data": {"error": str(e)}
    }

@router.get("/test-403")
async def test_403_endpoint():
  """Test endpoint to reproduce 403 error and debug"""
  try:
    from Config.config import KURAMANIME_URI
    from Config.config import responseRq
    
    # Test direct request to schedule endpoint
    test_url = f"{KURAMANIME_URI}/schedule?scheduled_day=Senin&page=1"
    logger.info(f"Testing direct request to: {test_url}")
    
    response = responseRq(test_url)
    
    return {
      "status": response.status_code,
      "message": "Test completed",
      "data": {
        "url": test_url,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content_length": len(response.text),
        "content_preview": response.text[:500] + "..." if len(response.text) > 500 else response.text
      }
    }
  except Exception as e:
    logger.error(f"403 test failed: {str(e)}")
    return {
      "status": 500,
      "message": "Test failed",
      "data": {"error": str(e)}
    }



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