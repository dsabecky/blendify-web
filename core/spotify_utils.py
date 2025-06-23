####################################################################
# Library & Modules
####################################################################

#system level stuff
import os
import time
from dotenv import load_dotenv

# data analysis
import requests
import base64

# parallels and retries
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff


####################################################################
# Environment Variables
####################################################################

load_dotenv()


####################################################################
# Functions
####################################################################

def can_retry(
    exception: Exception,
) -> bool:
    """
    Determines if an exception should be retried.

    Parameters:
        exception: The exception to check.

    Returns:
        True if the exception should be retried, False otherwise.
    """

    if isinstance(exception, requests.HTTPError):
        code = exception.response.status_code
        return code == 429 or 500 <= code < 600
    
    return False

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not can_retry(e))
def create_spotify_playlist(
    access_token: str,
    user_id: str,
    playlist_name: str,
) -> str:
    """
    Create a new Spotify playlist.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        user_id: The user's Spotify ID.
        playlist_name: The name of the playlist to create.

    Return:
    ---
        The ID of the created playlist.
    """
    
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = { "Authorization": f"Bearer {access_token}", "Content-Type": "application/json" }
    data = { "name": playlist_name, "description": "Created with Blendify. https://github.com/dsabecky/blendify-web", "public": True }
    response = requests.post(url, headers=headers, json=data)

    # retry if we're rate limited
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', '5'))
        time.sleep(retry_after)
        raise requests.HTTPError(response=response)
    
    # fail out due to an error
    elif response.status_code not in (200, 201):
        raise Exception(f"Failed to create playlist: {response.status_code} {response.text}")
    
    # return the playlistID
    playlist_data = response.json()
    return playlist_data['id']

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not can_retry(e))
def get_spotify_playlist_description(
    access_token: str,
    playlist_id: str,
) -> str | None:
    """
    Get the description of a Spotify playlist by playlistID.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        playlist_id: The ID of the playlist to get the description of.

    Returns:
    ---
        The description of the playlist, or None if the playlist is not found.
    """

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', '5'))
        time.sleep(retry_after)
        raise requests.HTTPError(response=response)

    elif response.status_code != 200:
        raise Exception(f"Failed to get playlist description: {response.status_code} {response.text}")
    
    data = response.json()
    return data.get("description")

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not can_retry(e))
def get_spotify_playlists(
    access_token: str,
    spotify_id: str,
) -> list[dict]:
    """
    Get the user's Spotify playlists that they can modify (owned or collaborative).

    Parameters:
    ---
        access_token: The user's Spotify access token.
        spotify_id: The user's Spotify ID.

    Returns:
    ---
        A list of dictionaries containing playlist IDs and names.
    """

    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = { "limit": 50 }

    playlists = []
    next_url = url
    while next_url:
        response = requests.get(next_url, headers=headers, params=data)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', '5'))
            time.sleep(retry_after)
            raise requests.HTTPError(response=response)

        elif response.status_code != 200:
            break

        data = response.json()
        for item in data.get('items', []):
            if item['owner']['id'] == spotify_id or item.get('collaborative', False):
                playlists.append({ 'id': item['id'], 'name': item['name'] })
        next_url = data.get('next')

    playlists.sort(key=lambda x: x['name'].lower())
    return playlists

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not can_retry(e))
def get_spotify_track_uri(
    access_token: str,
    song_title: str,
) -> str | None:
    """
    Get a trackURI from Spotify.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        song_title: The title of the song to search for.

    Returns:
    ---
        The URI of the track, or None if the track is not found.
    """

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = { "q": song_title, "type": "track", "limit": 1 }
    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', '5'))
        time.sleep(retry_after)
        raise requests.HTTPError(response=response)
    
    elif response.status_code != 200:
        return None
    
    data = response.json()
    items = data.get("tracks", {}).get("items", [])
    return items[0]["uri"] if items else None

def get_spotify_track_uris(
    access_token: str,
    songs: list[str],
) -> dict[str, str]:
    """
    Helper function for batch searching trackURIs.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        songs: The list of songs to search for.

    Returns:
    ---
        A dictionary of song titles and their corresponding trackURIs.
    """
    
    def search_single_song(song):
        return song, get_spotify_track_uri(access_token, song)
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_song = {
            executor.submit(search_single_song, song): song 
            for song in songs
        }
        
        for future in as_completed(future_to_song, timeout=30):
            try:
                song, uri = future.result()
                if uri:
                    results[song] = uri
            except Exception as e:
                song = future_to_song[future]
    
    return results

def update_spotify_access_token(
    user,
) -> bool:
    """
    Updates the Spotify access token if it's expired.

    Parameters:
    ---
        user: The user to update the access token for.
    Returns:
    ---
        Boolean indicating if the access token is valid or refreshed.
    """

    social = user.social_auth.filter(provider='spotify').first()
    if social.extra_data.get('auth_time') > time.time() - 3500:
        return True

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = { "Authorization": f"Basic {b64_credentials}", "Content-Type": "application/x-www-form-urlencoded" }
    data = {"grant_type": "refresh_token", "refresh_token": social.extra_data['refresh_token']}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"Failed to update access token: {response.status_code} {response.text}")

    social.extra_data['access_token'] = response.json()['access_token']
    social.extra_data['auth_time'] = int(time.time())
    social.extra_data = social.extra_data
    social.save()
    return True

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not can_retry(e))
def update_spotify_playlist(
    access_token: str,
    playlist_id: str,
    song_uris: list[str],
    playlist_name: str,
    playlist_description: str,
) -> bool:
    """
    Updates the playlist's name, description, and replaces all tracks with the provided URIs.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        playlist_id: The ID of the playlist to update.
        song_uris: The list of song URIs to add to the playlist.
        playlist_name: The name of the playlist to update.
        playlist_description: The description of the playlist to update.

    Returns:
    ---
        Boolean indicating if the playlist was updated successfully.
    """

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"name": playlist_name, "description": playlist_description}
    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', '5'))
        time.sleep(retry_after)
        raise requests.HTTPError(response=response)

    elif response.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist details: {response.status_code} {response.text}")

    valid_uris = [uri for uri in song_uris if uri and uri.startswith('spotify:track:')]
    
    if not valid_uris:
        raise Exception("No valid song URIs found to add to playlist")
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    data = { "uris": valid_uris[:100] }
    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', '5'))
        time.sleep(retry_after)
        raise requests.HTTPError(response=response)

    elif response.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist tracks: {response.status_code} {response.text}")

    return True