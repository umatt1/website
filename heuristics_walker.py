import spotipy
from spotipy import MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import json
import requests
import base64

with open("/etc/config.json") as config_file:
    config = json.load(config_file)
    CLIENT_ID = config.get("spotify_id")
    CLIENT_SECRET = config.get("spotify_secret")
    OAUTH_TOKEN = config.get("spotify_token")

scope = "playlist-modify-public"
redirect_uri = "https://www.umatt.me/spotify"
#manager = SpotifyOAuth(scope=scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri)
#spotify = spotipy.Spotify(client_credentials_manager=manager)

#username = "matt.burkhard@gmail.com"
#token = SpotifyOAuth(scope=scope, username=username, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri, show_dialog=False)
#print(token.get_access_token(as_dict=True))
#manager = SpotifyOAuth(scope=scope, username=username, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri, show_dialog=False, cache_handler=MemoryCacheHandler(token_info=token))
#spotify = spotipy.Spotify(client_credentials_manager=manager)

AUTH_URL = "https://accounts.spotify.com/authorize"
BASE_ADDR = "https://api.spotify.com"
TOKEN_URL = "https://accounts.spotify.com/api/token"
auth_response = requests.post(TOKEN_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET
})
auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}


def get_track(name):
    params = {'q':name, 'type':'track'}
    results = requests.get(BASE_ADDR + "/v1/search", headers=headers, params=params)
    results = results.json()
    items = results['tracks']['items']
    if len(items) > 0:
        return items[0:5]
    else:
        return None

def create_playlist(name, tracks):
    return None

def analytics(song):
    results = requests.get(BASE_ADDR + f"/v1/audio-features/{song['id']}", headers=headers).json()
    return results


def convergence(playlist1, playlist2):
    print(f"convergence on {playlist1[-1]['name']}, {playlist2[-1]['name']} => *{similarity(playlist1[-1], playlist2[-1])}*")
    return similarity(playlist1[-1], playlist2[-1]) <= .025


def similarity(song1, song2, URI=False):
    if not song1 or not song2:
        return 999999
    # if URI is true, passing URI directly
    if not URI:
        song1_heuristics = analytics(song1)
        song2_heuristics = analytics(song2)
    else:
        song1_heuristics = analytics(song1)
        song2_heuristics = analytics(song2)

    # we should do a least-squares type thing
    total = 0
    total += (song1_heuristics['danceability'] - song2_heuristics['danceability'])**2
    total += (song1_heuristics['energy'] - song2_heuristics['energy']) ** 2 # <- not a terrible heuristic?
    #total += (song1_heuristics['loudness'] - song2_heuristics['loudness']) ** 2 # <- spotify auto-adjusts for this I believe anyways so leave out
    total += (song1_heuristics['speechiness'] - song2_heuristics['speechiness']) ** 2 # <- I think this is good
    total += (song1_heuristics['acousticness'] - song2_heuristics['acousticness']) ** 2 # <- difficult to judge
    total += (song1_heuristics['instrumentalness'] - song2_heuristics['instrumentalness']) ** 2 # <- could be good to leave
    #total += (song1_heuristics['liveness'] - song2_heuristics['liveness']) ** 2 <- not a fan of this
    total += (song1_heuristics['valence'] - song2_heuristics['valence']) ** 2 # <- THIS IS GOOD

    # tempo is tricky. I think it matters but the weighting will be fridged if we do it the same as above
    # instead, consider dividing by the other and difference with one?
    # total += ((song1_heuristics['tempo'] / song2_heuristics['tempo'])-1) ** 2
    return total


def get_new_song(playlist, target_song):
    # given the playlist:
    #   1. generate recommendations for the playlist
    #   2. if the target song is found, return the target song <- this part could be optional
    #   3. run analytics on all of the recommendations, find the one with the most similarity using the audio stuff
    if len(playlist) < 5:
        ids = [x['id'] for x in playlist]
        ids = ",".join(ids)
        params = {'seed_tracks': ids, 'limit': 5}
    else:
        ids = [x['id'] for x in playlist]
        ids = ",".join(ids[-5:])
        params = {'seed_tracks': ids, 'limit': 5}

    results = requests.get(BASE_ADDR + "/v1/recommendations", params=params, headers=headers).json()
    results = results['tracks']

    if target_song in results:
        return target_song
    else:
        most_similar = None
        similarness = 99999999999
        for song in results:
            if song in playlist:
                continue
            song_similarness = similarity(song, target_song)
            if song_similarness < similarness:
                most_similar = song
                similarness = song_similarness
        print(f"added {most_similar['name']} with a similarity of {similarness} to {target_song['name']}")
        return most_similar


def walk_two_songs(song1, song2):
    """
    :param song1:
    :param song2:
    :return:

    Given two songs, walk from both ends towards spotify analytics that are more similar to the opposite song until
    some convergence is reached. This happens when the most recently added song (MRAS?) of both playlists have similar
    heuristics OR maybe the heuristics can't be made any more similar?
    """
    #song1 = spotify.track(song1)
    #song2 = spotify.track(song2)
    song1 = requests.get(BASE_ADDR + f"/v1/tracks/{song1}", headers=headers).json()
    song2 = requests.get(BASE_ADDR + f"/v1/tracks/{song2}", headers=headers).json()

    playlist1 = [song1]
    playlist2 = [song2]
    while not convergence(playlist1, playlist2):
        playlist1.append(get_new_song(playlist1, playlist2[-1]))
        playlist2.append(get_new_song(playlist2, playlist1[-1]))
    return playlist1+playlist2[::-1]

# tests
if __name__ == "__main__":
    beiber = "6rPO02ozF3bM7NnOV4h6s2"
    trevor_scoot = "2xLMifQCjDGFmkHkpNLD9h"
    #k=walk_two_songs(beiber, trevor_scoot)
    #post_malone = "0e7ipj03S05BNilyu5bRzt"
    #results = spotify.recommendations(seed_tracks=[beiber])
    #print(results.keys())
    #print(results['tracks'])
    #print(results['tracks'][0].keys())
    #print(results['tracks'][0]['uri'])
    #spotify.audio_analysis(track)
    #spotify.audio_features([tracks])
    #print(spotify.audio_analysis(results['tracks'][0]['uri']).keys())
    #print(spotify.audio_analysis(results['tracks'][0]['uri'])['segments'])
    #print(spotify.audio_features([results['tracks'][0]['uri']]))
    #song = get_track("beiber")[0]
    #a = analytics(song)
    #get_new_song([song], song)

    create_playlist("a", "a")

    #beiber_v_travis = similarity(beiber, trevor_scoot, URI=True)
    #beiber_v_post = similarity(beiber, post_malone, URI=True)
    #travis_v_post = similarity(post_malone, trevor_scoot, URI=True)

    #print(beiber_v_travis, beiber_v_post, travis_v_post)

    #my_name_is_jonas = {"id":'4nzyOwogJuWn1s6QuGFZ6w'}
    #sweater_song = {"id":'5WhtlIoxoZrMmuaWWEQhwV'}
    #island_in_the_sun = {"id":'2MLHyLy5z5l5YRp7momlgw'}
    #hurricane = {"id":'6Hfu9sc7jvv6coyy2LlzBF'}

    #print("jonas vs jonas", similarity(my_name_is_jonas, my_name_is_jonas, URI=False))
    #print("jonas vs sweater", similarity(my_name_is_jonas, sweater_song, URI=False))
    #print("jonas vs island", similarity(my_name_is_jonas, island_in_the_sun, URI=False))
    #print("jonas vs hurricane", similarity(my_name_is_jonas, hurricane, URI=False))

    #create_playlist("test_playlist", [my_name_is_jonas, sweater_song, island_in_the_sun, hurricane])