from datetime import datetime, timedelta
from hashlib import md5
import requests
import os
import base64

def get_auth_code_obj(spotify_code):
    if spotify_code is None:
        return
    url = 'https://accounts.spotify.com/api/token'
    redirect_url = os.getenv('APP_BASE_URL')+'/spotify/auth/callback/'
    body = {
        'redirect_uri': redirect_url,
        'grant_type': 'authorization_code',
        'code': spotify_code
    }
    auth_code_req = requests.post(url, headers=get_header(), data=body)
    return auth_code_req.json()

def get_refresh_token(refresh_token):
    if refresh_token is None:
        return
    url = 'https://accounts.spotify.com/api/token'
    body = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    return requests.post(url, headers=get_header(), data=body).json()


def get_header():
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    spotify_app_base64 = base64_string(f'{CLIENT_ID}:{CLIENT_SECRET}')
    return {
        'Authorization': f'Basic {spotify_app_base64}'
    }

def get_token_header(access_token):
    return {
        'Authorization': f'Bearer {access_token}'
    }

def time_difference_in_minutes(date):
    current_time = datetime.now()
    difference = date.replace(tzinfo=None) - current_time.replace(tzinfo=None)
    total_minutes = difference.total_seconds() / 60
    return total_minutes

def get_expired_date(seconds):
    current_time = datetime.now()
    result_time = current_time + timedelta(seconds=seconds)
    return result_time

def base64_string(string):
    encoded_string = base64.b64encode(string.encode('utf-8'))
    return encoded_string.decode('utf-8')

# def check_authentication(session):
#     if session.get('access_token_obj') is None:
#         return None
#     if time_difference_in_minutes(session['access_token_obj']['expire_date']) < 1:
#         session['access_token_obj'] = get_refresh_token(session['access_token_obj']['refresh_token'])
#         session['access_token'] = session['access_token_obj']['access_token']
#         session['access_token_obj']['expire_date'] = get_expired_date(session['access_token_obj']['expires_in'])
#     return True

def extract_track(track):
    return {
        'id': track['id'],
        'name': track['name'],
        'url': track['external_urls']['spotify'],
        'cover_url': track['album']['images'][0],
        'artist': track['artists'],
        'explicit': track['explicit'],
        'album_name': track['album']['name'],
        'uri': track['uri']
    }

def get_track_hash(track):
    track_name = track['name']
    artist_names = ''
    album_name = track['album']['name']
    for artist in track['artists']:
        artist_names += artist['name']
    track_string = f"{track_name}{artist_names}{album_name}"
    # print(track_string, track['explicit'])
    return md5(track_string.encode('utf-8')).hexdigest()

from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))