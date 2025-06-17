import requests

def get_spotify_playlist_description(
    user,
    playlist_id: str,
) -> str | None:
    """
    Returns the description of a Spotify playlist by ID for the given user.
    """
    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        return None
    access_token = social.extra_data['access_token']
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    data = resp.json()

    return data.get("description")

def get_spotify_playlists(
    user,
) -> list[dict]:
    """
    Get the user's Spotify playlists.
    """
    # Get the user's Spotify social auth
    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        return []
    access_token = social.extra_data['access_token']
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
            playlists.append({
                'id': item['id'],
                'name': item['name'],
            })
        next_url = data.get('next')

    playlists.sort(key=lambda x: x['name'].lower())
    return playlists

def get_spotify_song_uri(
    user,
    song_title: str,
) -> str | None:
    """
    Given a user and a song title (e.g., "blink-182 - all the small things"),
    returns the Spotify track URI if found, else None.
    """
    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        return None
    access_token = social.extra_data['access_token']

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": song_title,
        "type": "track",
        "limit": 1,
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        return None
    data = resp.json()
    items = data.get("tracks", {}).get("items", [])
    if not items:
        return None
    
    return items[0]["uri"]

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
    # Get the user's Spotify access token
    social = user.social_auth.filter(provider='spotify').first()
    if not social:
        raise Exception("User not authenticated with Spotify.")
    access_token = social.extra_data['access_token']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 1. Update playlist name and description
    details_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    details_data = {
        "name": playlist_name,
        "description": playlist_description
    }
    details_resp = requests.put(details_url, headers=headers, json=details_data)
    if details_resp.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist details: {details_resp.status_code} {details_resp.text}")

    # 2. Replace all tracks in the playlist (up to 100)
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    tracks_data = {
        "uris": song_uris[:100]
    }
    tracks_resp = requests.put(tracks_url, headers=headers, json=tracks_data)
    if tracks_resp.status_code not in (200, 201):
        raise Exception(f"Failed to update playlist tracks: {tracks_resp.status_code} {tracks_resp.text}")

    return True