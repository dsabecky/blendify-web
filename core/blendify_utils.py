####################################################################
# Library & Modules
####################################################################

# system level stuff
import os
import dotenv

# data analysis
import random

# parallel processing
from concurrent.futures import ThreadPoolExecutor, as_completed

# blendify specific imports
from core.openai_utils import generate_chatgpt_playlist, generate_chatgpt_playlist_description, generate_chatgpt_playlist_name, invoke_chatgpt
from core.spotify_utils import get_spotify_playlist_description, get_spotify_track_uris
from core.models import Playlist, Song


####################################################################
# Environment Variables
####################################################################

dotenv.load_dotenv()


####################################################################
# Functions
####################################################################

def build_individual_playlists(
    themes: list[str],
) -> dict[str, list[str]]:
    """
    Handler function for batch processing of ChatGPT generated playlists.
    
    Parameters:
    ---
        themes: A list of themes to build playlists for.

    Returns:
    ---
        A dictionary of themes, with their corresponding playlist.
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(build_individual_playlist, theme): theme for theme in themes}
        results = {futures[future]: future.result() for future in as_completed(futures)}
    return results

def build_individual_playlist(
    theme: str,
) -> list[str]:
    """
    Build an individual playlist for a given theme using ChatGPT.

    Parameters:
    ---
        theme: The theme to build a playlist for.

    Returns:
    ---
        A list of songs.
    """

    existing = Playlist.objects.filter(theme__iexact=theme).first()
    if existing:
        songs = existing.song_list
    else:
        conversation = generate_chatgpt_playlist(theme)
        songs = [song.strip() for song in invoke_chatgpt(conversation).splitlines() if song.strip()]
        Playlist.objects.create(theme=theme.lower(), song_list=songs)

    return songs

def build_combined_playlist(
    individual_playlists: dict[str, list[str]],
) -> list[str]:
    """
    Build a combined playlist from the individual playlists with even distribution.

    Parameters:
    ---
        individual_playlists: A dictionary of themes, with their corresponding playlist.

    Returns:
    ---
        A list of songs.
    """

    total_length = int(os.getenv('PLAYLIST_LENGTH', 10))
    sample_size = total_length // len(individual_playlists)
    remainder = total_length % len(individual_playlists)
    
    combined_playlist = []
    used_songs = set()
    
    for i, playlist in enumerate(individual_playlists):
        current_sample_size = sample_size + (1 if i < remainder else 0)
        
        unique_songs = [song for song in playlist if song.lower() not in used_songs]
        
        random.shuffle(unique_songs)
        selected_songs = unique_songs[:current_sample_size]
        
        combined_playlist.extend(selected_songs)
        used_songs.update(song.lower() for song in selected_songs)
        
    if len(combined_playlist) < total_length:
        all_remaining = []
        for playlist in individual_playlists.values():
            all_remaining.extend([song for song in playlist if song.lower() not in used_songs])
        
        random.shuffle(all_remaining)
        needed = total_length - len(combined_playlist)
        combined_playlist.extend(all_remaining[:needed])
    
    return combined_playlist

def build_playlist_name(
    combined_playlist: list[str],
    spotify_playlist_name: str,
    playlist_rename: bool,
) -> str:
    """
    Build a name for a combined playlist.

    Parameters:
    ---
        combined_playlist: A list of songs.
        spotify_playlist_name: The name of the Spotify playlist.
        playlist_rename: Whether to rename the playlist.

    Returns:
    ---
        A string of the playlist name.
    """
    if playlist_rename:
        return invoke_chatgpt(generate_chatgpt_playlist_name(combined_playlist))
    else:
        return spotify_playlist_name
    
def build_playlist_description(
    access_token: str,
    combined_playlist: list[str],
    spotify_playlist_id: str,
    playlist_rename: bool,
) -> str | None:
    """
    Build a description for a combined playlist.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        combined_playlist: A list of songs.
        spotify_playlist_id: The ID of the Spotify playlist.
        playlist_rename: Whether to rename the playlist.

    Returns:
    ---
        A string of the playlist description.
    """
    if playlist_rename:
        return invoke_chatgpt(generate_chatgpt_playlist_description(combined_playlist))
    else:
        return get_spotify_playlist_description(access_token, spotify_playlist_id)

def build_song_uris(
    access_token: str,
    song_list: list[str],
) -> list[str]:
    """
    Get URIs for songs using batch processing.

    Parameters:
    ---
        access_token: The user's Spotify access token.
        song_list: A list of songs.

    Returns:
    ---
        A list of song URIs.
    """
    if not song_list:
        return []
    
    cached_songs = {}
    existing_songs = Song.objects.filter(
        name__iregex=r'^(' + '|'.join([
            song.replace('(', r'\(').replace(')', r'\)').replace('[', r'\[').replace(']', r'\]')
            for song in song_list
        ]) + ')$'
    ).values('name', 'spotify_uri')
    
    for song_obj in existing_songs:
        for original_song in song_list:
            if song_obj['name'].lower() == original_song.lower() and song_obj['spotify_uri']:
                cached_songs[original_song] = song_obj['spotify_uri']
                break
    
    uncached_songs = [song for song in song_list if song not in cached_songs]
    
    if uncached_songs:
        new_uris = get_spotify_track_uris(access_token, uncached_songs)
        
        songs_to_create = []
        for song, uri in new_uris.items():
            if uri:
                songs_to_create.append(Song(name=song, spotify_uri=uri))
                cached_songs[song] = uri
        
        if songs_to_create:
            try:
                Song.objects.bulk_create(songs_to_create, ignore_conflicts=True)
            except Exception as e:
                print(f"Error bulk creating songs: {e}")
                for song_obj in songs_to_create:
                    try:
                        Song.objects.get_or_create(
                            name__iexact=song_obj.name,
                            defaults={'name': song_obj.name, 'spotify_uri': song_obj.spotify_uri}
                        )
                    except Exception:
                        pass  # Skip problematic songs
    
    return [cached_songs.get(song) for song in song_list if cached_songs.get(song)]