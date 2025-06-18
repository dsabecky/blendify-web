import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_spotify_playlist(
    user,
    playlist_name: str
) -> str:
    """
    Create a new Spotify playlist and return its ID.
    """

    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    
    access_token = social.extra_data['access_token']
    spotify_user_id = social.uid
    
    url = f"https://api.spotify.com/v1/users/{spotify_user_id}/playlists"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": playlist_name,
        "description": "Created with Blendify (https://github.com/dsabecky/blendify-web)",
        "public": True
    }
    
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to create playlist: {resp.status_code} {resp.text}")
    
    playlist_data = resp.json()
    return playlist_data['id']

def fetch_song_uri(
    access_token: str,
    song_title: str,
) -> str | None:
    """
    Direct Spotify search without user object dependency.
    """

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": song_title,
        "type": "track",
        "limit": 1,
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 429:
            raise Exception("Rate limited")
        elif resp.status_code != 200:
            return None
        
        data = resp.json()
        items = data.get("tracks", {}).get("items", [])
        return items[0]["uri"] if items else None
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout searching for song")
    except Exception:
        return None

def get_spotify_playlist_description(
    user,
    playlist_id: str,
) -> str | None:
    """
    Returns the description of a Spotify playlist by ID for the given user.
    """
    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    
    access_token = social.extra_data['access_token']

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to get playlist description: {resp.status_code} {resp.text}")
    data = resp.json()

    return data.get("description")

def get_spotify_playlists(
    user,
) -> list[dict]:
    """
    Get the user's Spotify playlists that they can modify (owned or collaborative).
    """

    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    
    access_token = social.extra_data['access_token']
    spotify_id = social.uid

    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}

    playlists = []
    next_url = url
    while next_url:
        resp = requests.get(next_url, headers=headers)
        if resp.status_code != 200:
            break
        data = resp.json()
        for item in data.get('items', []):
            if item['owner']['id'] == spotify_id or item.get('collaborative', False):
                playlists.append({
                    'id': item['id'],
                    'name': item['name'],
                })
        next_url = data.get('next')

    playlists.sort(key=lambda x: x['name'].lower())
    return playlists

def get_spotify_song_uris(
    user,
    songs: list[str],
) -> dict[str, str]:
    """
    Search multiple songs concurrently using ThreadPoolExecutor.
    """

    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    
    access_token = social.extra_data['access_token']
    
    def search_single_song(song):
        return song, fetch_song_uri(access_token, song)
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
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

def update_spotify_playlist(
    user,
    playlist_id: str,
    song_uris: list[str],
    playlist_name: str,
    playlist_description: str,
) -> bool | None:
    """
    Updates the playlist's name, description, and replaces all tracks with the provided URIs.
    """

    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    access_token = social.extra_data['access_token']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    details_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    details_data = {
        "name": playlist_name,
        "description": playlist_description
    }
    details_resp = requests.put(details_url, headers=headers, json=details_data)
    if details_resp.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist details: {details_resp.status_code} {details_resp.text}")

    valid_uris = [uri for uri in song_uris if uri and uri.startswith('spotify:track:')]
    
    if not valid_uris:
        raise Exception("No valid song URIs found to add to playlist")
    
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    tracks_data = {
        "uris": valid_uris[:100]
    }
    tracks_resp = requests.put(tracks_url, headers=headers, json=tracks_data)
    if tracks_resp.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist tracks: {tracks_resp.status_code} {tracks_resp.text}")

    return True