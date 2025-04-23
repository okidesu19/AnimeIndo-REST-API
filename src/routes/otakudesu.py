from flask import Blueprint, render_template
import requests
#src
from src.parser.Otakudesu.otakudesu import ongoing, genres, detail, episode, property_genre

otakudesu_print = Blueprint('otakudesu', __name__)

#> ONGOING
@otakudesu_print.route('/ongoing/')
def ongoing_route():
  data = ongoing()
  return data

@otakudesu_print.route('/genres/')
def genres_route():
  return genres()

@otakudesu_print.route('/anime/<animeSlug>/')
def detail_route(animeSlug):
  return detail(animeSlug)
  
@otakudesu_print.route('/watch/<episodeSlug>/')
def episode_route(episodeSlug):
  return episode(episodeSlug)
  
@otakudesu_print.route('/genre/<genreSlug>/')
def property_genre_route(genreSlug):
  return property_genre(genreSlug)


#>>> WEB

