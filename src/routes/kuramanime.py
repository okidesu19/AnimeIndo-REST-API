from flask import Blueprint
from src.parser.Kuramanime.kuramanime import animeView, genres, shedule, search, propertyGenre, animeDetail, streamingUrl

kuramanime_print = Blueprint('kuramanime', __name__)

@kuramanime_print.route('/view/<view>/', defaults={'order_by' : 'latest'})
@kuramanime_print.route('/view/<view>/<order_by>/')
def animeView_route(view, order_by):
  return animeView(view, order_by)


@kuramanime_print.route('/genres/', methods=['GET'])
def genres_route():
  return genres()


@kuramanime_print.route('/shedule/<hari>/', defaults={'page' : 1})
@kuramanime_print.route('/shedule/<hari>&page=<page>')
def shedule_route(hari, page):
  return shedule(hari, page)


@kuramanime_print.route('/search/<kwy>?order_by=<order_by>/', defaults={'page' : 1})
@kuramanime_print.route('/search/<kwy>?order_by=<order_by>&page=<page>')
def search_route(kwy, order_by, page):
  return search(kwy, order_by, page)


@kuramanime_print.route('/genre/<genre>/order_by=<order_by>/', defaults={'page' : 1})
@kuramanime_print.route('/genre/<genre>/order_by=<order_by>&page=<page>/')
def propertyGenre_route(genre, order_by, page):
  return propertyGenre(genre, order_by, page)


@kuramanime_print.route('/anime/<animeId>/<animeSlug>/')
def detail_route(animeId, animeSlug):
  return animeDetail(animeId, animeSlug)

@kuramanime_print.route('/anime/<animeId>/<animeSlug>/episode/<episodeId>')
def streaming_route(animeId, animeSlug, episodeId):
  return streamingUrl(animeId, animeSlug, episodeId)
  

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