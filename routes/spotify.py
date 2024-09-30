from flask import Blueprint, request, session, redirect, jsonify
from urllib.parse import urlencode
from utils.spotify import get_auth_code_obj, get_token_header, get_expired_date, extract_track, get_track_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, unset_jwt_cookies
from datetime import datetime
import os
import requests
import math

auth_app = Blueprint('auth', __name__)

@auth_app.route('/auth', methods=["GET", "POST"])
def spotify_auth():
    redirect_url = os.getenv('APP_BASE_URL')+'/spotify/auth/callback/'
    query_parameters = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': redirect_url,
        'scope': 'playlist-modify-public playlist-modify-private playlist-read-collaborative playlist-read-private',
    }
    spotify_url = 'https://accounts.spotify.com/authorize?' + urlencode(query_parameters)
    session['referrer_url'] = request.referrer
    return redirect(spotify_url)
    # return {'status':200, 'message': spotify_url}

@auth_app.route('/auth/callback/', methods=["GET"])
def spotify_callback():
    d = {
        'status': 200,
        'message': 'Logged into spotify successfully.'
    }
    if request.args.get("code") is None:
        d['status'] = 401
        d['message'] = 'Not logged into Spotify' 
    else:
        spotify_code = request.args["code"]
        access_token_obj = get_auth_code_obj(spotify_code)
        # access_token = access_token_obj['access_token']
        access_token_obj['expire_date'] = get_expired_date(access_token_obj['expires_in'])
        # d['code'] = session['spotify_code']
    resp = redirect(session['referrer_url'])
    resp.set_cookie('jwt', create_access_token(access_token_obj))
    return resp

@auth_app.route('/auth/logout', methods=["GET"])
def spotify_logout():
    d = jsonify({'status': 200, 'message': 'Logged out of Spotify successfully'})
    session.clear()
    unset_jwt_cookies(d)
    resp = redirect(request.referrer)
    resp.set_cookie('jwt', expires=datetime.now())
    return resp

@auth_app.route('/authenticated', methods=["GET"])
@jwt_required()
def spotify_authenticated():
    return {'status': 200, 'authenticated': True}

@auth_app.route('/playlists', methods=["GET", "PUT"])
@jwt_required()
def all_spotify_playlists():
    jwt_data = get_jwt_identity()
    header = get_token_header(jwt_data['access_token'])
    if request.method == 'GET':
        page_args = request.args.get("page")
        page = 0
        if  page_args is not None: page = (int(page_args)-1) * 10
        url = f'https://api.spotify.com/v1/me/playlists?offset={page}&limit=10'
        playlist_response = requests.get(url, headers=header)
        return playlist_response.json()
    elif request.method == 'PUT':
        request_data = request.get_json()
        url = f'https://api.spotify.com/v1/me'
        r = requests.get(url, headers=header)
        user_id = r.json()['id']
        url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        playlist_data = {
            'name': request_data['playlist_name'],
            'description': request_data['description'],
            'public': False
        }
        r = requests.post(url, json=playlist_data, headers=header)
        new_playlist_id = r.json()['id']
        new_track_ids = request_data['ids']
        request_num = math.ceil(len(new_track_ids) / 100)
        startIndex = 0
        endIndex = 100
        url = f'https://api.spotify.com/v1/playlists/{new_playlist_id}/tracks'
        for i in range(request_num):
            r = requests.post(url, json=new_track_ids[startIndex:endIndex], headers=header)
            tempIndex = endIndex
            startIndex = tempIndex + 1
            endIndex = tempIndex + 100
        # return {'playlistID': True}, 200
        return {'playlistID': new_playlist_id}, 200

@auth_app.route('/playlists/<pid>', methods=["GET"])
@jwt_required()
def get_spotify_playlist(pid):
    jwt_data = get_jwt_identity()
    url = f'https://api.spotify.com/v1/playlists/{pid}'
    header = get_token_header(jwt_data['access_token'])
    playlist_response = requests.get(url, headers=header)
    return playlist_response.json()

@auth_app.route('/playlists/<pid>/tracks', methods=["GET"])
@jwt_required()
def get_spotify_playlist_tracks(pid):
    jwt_data = get_jwt_identity()
    tracks = {'items': []}
    next = True
    first = True
    url = ''
    while next:
        if first:
            url = f'https://api.spotify.com/v1/playlists/{pid}/tracks'
            first = False
        header = get_token_header(jwt_data['access_token'])
        playlist_track_response = requests.get(url, headers=header).json()
        tracks['items'].extend(playlist_track_response['items'])
        url = playlist_track_response.get('next')
        if playlist_track_response['next'] is None:
            tracks['playlist'] = get_spotify_playlist(pid)
            next = False
            continue
    return tracks

@auth_app.route('/tracks/<tid>', methods=["GET"])
@jwt_required()
def get_spotify_tracks(tid):
    url = f'https://api.spotify.com/v1/tracks/{tid}'
    header = get_token_header(session['access_token'])
    track_response = requests.get(url, headers=header).json()
    return extract_track(track_response)
    # return track_response

@auth_app.route('/tracks/<tid>/clean', methods=["GET"])
@jwt_required()
def search_spotify_clean_tracks(tid):
    url = f'https://api.spotify.com/v1/tracks/{tid}'
    header = get_token_header(get_jwt_identity()['access_token'])
    track_response = requests.get(url, headers=header).json()
    if not track_response['explicit']:
        return {'items': track_response, 'exact_match': True}
    current_track_hash = get_track_hash(track_response)

    artist_query = ''
    for artist in track_response['artists']:
        artist_query += f"{artist['name']} "
    search_query = f"{track_response['name']} {artist_query}"
    search_url = f'https://api.spotify.com/v1/search?q={search_query}&type=track&limit=5'
    search_response = requests.get(search_url, headers=header).json()
    search_response_obj = list()
    for result in search_response['tracks']['items']:
        if not result['explicit']:
            track_hash = get_track_hash(result)
            search_response_obj.append(extract_track(result))
            if track_hash == current_track_hash:
               return {'items': extract_track(result), 'exact_match': True}
    
    return {'items': search_response_obj, 'exact_match': False}

# @auth_app.route('/playlists/<pid>/clean', methods=["GET"])
# @jwt_required()
# def clean_spotify_playlist(pid):
#     tracks = list()
#     next = True
#     first = True
#     url = ''
#     while next:
#         if first:
#             url = f'https://api.spotify.com/v1/playlists/{pid}/tracks'
#             first = False
#         header = get_token_header(session['access_token'])
#         playlist_track_response = requests.get(url, headers=header).json()
#         tracks.extend(playlist_track_response['items'])
#         url = playlist_track_response.get('next')
#         print(url)
#         if playlist_track_response['next'] is None:
#             next = False
#             continue
#     return tracks
