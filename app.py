#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from itertools import groupby
from operator import attrgetter
from models import db, Artist, Venue, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# Create tables
app.app_context().push()
db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  # Query database. Ordered by city and state for use as key in groupby()
  venues = Venue.query.order_by('city', 'state', 'name').all()
  # Group venues into areas by city and state.
  for area, venuesInArea in groupby(venues, lambda a: (a.city, a.state)):
     data.append({
        "city": area[0], # index 0 = city
        "state": area[1], # index 1 = state
        "venues": list(venuesInArea)
      })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  page_data = []
  search_term = request.form.get('search_term', '')
  search_expression = '%' + search_term + '%'
  venues = Venue.query.filter(Venue.name.ilike(search_expression)).order_by('name').all()

  for venue in venues:
     upcoming_show_count = 0

     for show in venue.shows:
        if show.start_time > datetime.now():
           upcoming_show_count += 1
           
     page_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming_show_count
     })

  response={
    "count": len(venues),
    "data": page_data,
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data = Venue.query.get(venue_id)
  data.genres = data.genres.split(',')
  upcoming_shows = []
  past_shows = []
  for show in data.shows:
    if show.start_time > datetime.now():
      show.start_time = str(show.start_time)
      show.artist_image_link = show.Artist.image_link
      show.artist_name = show.Artist.name
      upcoming_shows.append(show)
    else:
      show.start_time = str(show.start_time)
      show.artist_image_link = show.Artist.image_link
      show.artist_name = show.Artist.name
      past_shows.append(show)
  data.upcoming_shows = upcoming_shows
  data.past_shows = past_shows

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  form = VenueForm(request.form)
  try:
     if form.validate:
      genres=','.join(form.genres.data)
      venue = Venue(
         name=form.name.data,
         genres=genres,
         city=form.city.data,
         state=form.state.data,
         address=form.address.data,
         phone=form.phone.data,
         website=form.website_link.data,
         image_link=form.image_link.data,
         facebook_link=form.facebook_link.data,
         seeking_talent=form.seeking_talent.data,
         seeking_description=form.seeking_description.data,
      )
      db.session.add(venue)
      db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # on unsuccessful db insert, flash an error.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    abort(500)
  else:
     # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try: 
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
     db.session.close()
  if error:
     flash('An error occurred. Venue ' + venue.name + ' could not be deleted')
     abort(500)
  else:
     flash('Venue ' + venue.name + ' deleted sucessfully!')
  
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.order_by('name').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  page_data = []
  search_term = request.form.get('search_term', '')
  search_expression = '%' + search_term + '%'
  artists = Artist.query.filter(Artist.name.ilike(search_expression)).order_by('name').all()

  for artist in artists:
     upcoming_show_count = 0

     for show in artist.shows:
        if show.start_time > datetime.now():
           upcoming_show_count += 1
           
     page_data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": upcoming_show_count
     })

  response={
    "count": len(artists),
    "data": page_data,
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.get(artist_id)
  data.genres = data.genres.split(',')
  upcoming_shows = []
  past_shows = []
  for show in data.shows:
    if show.start_time > datetime.now():
      show.start_time = str(show.start_time)
      show.venue_image_link = show.Venue.image_link
      show.venue_name = show.Venue.name
      upcoming_shows.append(show)
    else:
      show.start_time = str(show.start_time)
      show.venue_image_link = show.Venue.image_link
      show.venue_name = show.Venue.name
      past_shows.append(show)
  data.upcoming_shows = upcoming_shows
  data.past_shows = past_shows

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm()
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres.split(',')
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  form = ArtistForm(request.form)
  try:
     if form.validate:
      listGenres = form.genres.data
      genres = ','.join(listGenres)
      artist = Artist.query.get(artist_id)
      artist.name=form.name.data
      artist.city=form.city.data
      artist.state=form.state.data
      artist.phone=form.phone.data
      artist.genres=genres
      artist.image_link=form.image_link.data
      artist.website=form.website_link.data
      artist.facebook_link=form.facebook_link.data
      artist.seeking_venue=form.seeking_venue.data
      artist.seeking_description=form.seeking_description.data
      db.session.commit()
  except:
     error = True
     db.session.rollback()
     print(sys.exc_info())
  finally:
     db.session.close()
  if error:
     abort(500)
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.genres.data = venue.genres.split(',')
  form.image_link.data = venue.image_link
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  form = VenueForm(request.form)
  try:
     if form.validate:
      listGenres = form.genres.data
      genres = ','.join(listGenres)
      venue = Venue.query.get(venue_id)
      venue.name=form.name.data
      venue.city=form.city.data
      venue.state=form.state.data
      venue.address=form.address.data
      venue.phone=form.phone.data
      venue.genres=genres
      venue.image_link=form.image_link.data
      venue.website=form.website_link.data
      venue.facebook_link=form.facebook_link.data
      venue.seeking_talent=form.seeking_talent.data
      venue.seeking_description=form.seeking_description.data
      db.session.commit()
  except:
     error = True
     db.session.rollback()
     print(sys.exc_info())
  finally:
     db.session.close()
  if error:
     abort(500)
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  form = ArtistForm(request.form)
  try:
     if form.validate:
      listGenres = form.genres.data
      genres = ','.join(listGenres)
      artist = Artist(
          name=form.name.data,
          city=form.city.data,
          state=form.state.data,
          phone=form.phone.data,
          genres=genres,
          image_link=form.image_link.data,
          website=form.website_link.data,
          facebook_link=form.facebook_link.data,
          seeking_venue=form.seeking_venue.data,
          seeking_description=form.seeking_description.data,
      )
      db.session.add(artist)
      db.session.commit()
  except:
     error = True
     db.session.rollback()
     print(sys.exc_info())
  finally:
     db.session.close()
     if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash ('An error occured. Artist ' + request.form['name'] + ' could not be created.')
     else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = Show.query.order_by('start_time').all()
  for show in shows:
     data.append({
        "venue_id": show.Venue.id,
        "venue_name": show.Venue.name,
        "artist_id": show.Artist.id,
        "artist_name": show.Artist.name,
        "artist_image_link": show.Artist.image_link,
        "start_time": format_datetime(str(show.start_time))
     })
     
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  form = ShowForm(request.form)
  try:
     if form.validate:
        show = Show(
           artist_id = form.artist_id.data,
           venue_id = form.venue_id.data,
           start_time = form.start_time.data,
        )
        db.session.add(show)
        db.session.commit()
  except:
    error = True
    abort(500)
  finally:
     db.session.close()
  if error:
     # on unsuccessful db insert, flash an error instead.
     flash('An error occurred. Show could not be listed')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
     
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
