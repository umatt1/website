import argparse
from heuristics_walker import walk_two_songs, \
    similarity, CLIENT_ID, CLIENT_SECRET, OAUTH_TOKEN, create_playlist, redirect_uri, get_track


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a')
    parser.add_argument('-b')
    args = parser.parse_args()
    start_song = get_track(args.a)[0]
    end_song = get_track(args.b)[0]
    print(f"Starting at {start_song['name']} by {start_song['artists'][0]['name']} ({start_song['id']})")
    print(f"Ending at {end_song['name']} by {end_song['artists'][0]['name']} ({end_song['id']})")
    final_playlist = walk_two_songs(start_song, end_song)
    prev = final_playlist[-1]
    for ind, track in enumerate(final_playlist):
        print(f"{ind+1}. {track['name']} by {track['artists'][0]['name']} ({similarity(track, prev)})")
        prev = track

if __name__ == "__main__":
    main()