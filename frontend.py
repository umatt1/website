from flask import Flask, Blueprint, request, redirect, url_for, render_template, session, g
from commandline_interface import walk_two_songs, get_track, create_playlist, redirect_uri
import requests
from urllib.parse import quote
import json

spotify = Blueprint("spotify", __name__, template_folder='templates')


@spotify.route("/verify/<searchstring>", methods=['POST','GET'])
def verify_tracks(searchstring):
    # this page will display up to 5 search queries for the up to 5 listed anchors
    searchstring=searchstring.split(",")

    if len(searchstring) > 5:
        return "only 5 anchors allowed"

    if request.method == 'POST':
        # from this spot, we need to feed the data into the next page
        tracks = []
        for i, search in enumerate(searchstring):
            # we need to:
            #   1. check the set of radios
            #   2. identify which is selected
            #   3. append the correct values into tracks
            id = request.form[f'options{i}']
            tracks.append(id)
        tracksstring = "|"
        tracksstring = tracksstring.join(tracks)
        return redirect(url_for("spotify.spotify_tracks", tracks=tracksstring))
    else:
        queries = []
        print(redirect_uri)
        for search in searchstring:
            results = get_track(search)
            if not results:
                return f"could not find any results for {search}. please try again."
            queries.append(results)
        values = range(0, len(queries))
        return render_template("verification_page.html", queries=queries, values=values)


@spotify.route("/", methods=['POST', 'GET'])
def spotify_home():
    if request.method == 'POST':
        tracks = request.form['tracks']
        return redirect(url_for("spotify.verify_tracks",searchstring=tracks))
    else:
        return render_template("spotify_home.html")


@spotify.route("/tracks/<tracks>", methods=["POST","GET"])
def spotify_tracks(tracks):
    if request.method == 'POST':
        playlist = session['total_playlist']
        return redirect(url_for("spotify.authorize"))
    else:
        tracks = tracks.split("|")
        print(tracks)
        # currently, we have a list of track ids. the idea here is:
        #   1. walk between every track to create a playlist
        #   2. create a spotify playlist
        total_playlist = []
        last_track = None
        for ind, track in enumerate(tracks):
            if ind == len(tracks)-1:
                continue
            next_track = tracks[ind+1]
            walk = walk_two_songs(track, next_track)
            total_playlist.extend(walk[:-1])
            last_track = walk[-1]
        total_playlist.append(last_track)

        to_return_test = ""
        for track in total_playlist:
            to_return_test += f"<p>{track['name']} by {track['artists'][0]['name']}</p>"
        # all we need now is to create a spotify playlist
        session['total_playlist'] = [x['id'] for x in total_playlist]
        session['start'] = total_playlist[0]['name']
        session['end'] = total_playlist[-1]['name']
        values = range(0, len(total_playlist))
        return render_template("display_playlist.html", total_playlist=total_playlist, values=values)




# the rest of this is coming from some other stuff
# https://github.com/drshrey/spotify-flask-auth-example
with open("/etc/config.json") as config_file:
    #  Client Keys
    config = json.load(config_file)
    CLIENT_ID = config.get("spotify_id")
    CLIENT_SECRET = config.get("spotify_secret")

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "https://www.umatt.me"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}


@spotify.route("/authorize/")
def authorize():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@spotify.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # create playlists
    user_id = profile_data['id']
    user_create_playlist_endpoint = f"{SPOTIFY_API_URL}/users/{user_id}/playlists"
    data = {
        "name": "test",
        "public": True,
        "collaborative": False,
        "description": "created at umatt.me/spotify"
    }
    create_playlist_response = requests.post(user_create_playlist_endpoint, headers=authorization_header, payload=data)


    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data["items"]
    return display_arr


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(spotify)
    with open("/etc/config.json") as config:
        config = json.load(config)
        session_key = config.get("session_key")
    app.secret_key = session_key
    '''
    app.config.update(
        SESSION_PERMANENT=False,
        SESSION_TYPE="filesystem"
    )
    '''
    app.run(debug=True)