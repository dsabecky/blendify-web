from core.openai_utils import generate_chatgpt_playlist, generate_chatgpt_playlist_description, generate_chatgpt_playlist_name, invoke_chatgpt
from core.spotify_utils import get_spotify_playlist_description, get_spotify_song_uri

from core.models import Playlist, Song
import random
import os
import dotenv

dotenv.load_dotenv()

def build_individual_playlist(
    theme: str,
) -> list[str]:
    """
    Build individual playlists for each theme.
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
    Build a combined playlist from the individual playlists.
    """
    sample_size = int(int(os.getenv('PLAYLIST_LENGTH', 10)) / len(individual_playlists))

    combined_playlist = []
    for playlist in individual_playlists.values():
        unique_songs = [song for song in playlist if song not in combined_playlist]

        random.shuffle(unique_songs)
        combined_playlist.extend(unique_songs[:sample_size])

    return combined_playlist

def build_playlist_name(
    combined_playlist: list[str],
    spotify_playlist_name: str,
    playlist_rename: bool,
) -> str:
    """
    Build a name for a combined playlist.
    """
    if playlist_rename:
        return invoke_chatgpt(generate_chatgpt_playlist_name(combined_playlist))
    else:
        return spotify_playlist_name
    
def build_playlist_description(
    user,
    combined_playlist: list[str],
    spotify_playlist_id: str,
    playlist_rename: bool,
) -> str | None:
    """
    Build a description for a combined playlist.
    """
    if playlist_rename:
        return invoke_chatgpt(generate_chatgpt_playlist_description(combined_playlist))
    else:
        return get_spotify_playlist_description(user, spotify_playlist_id)

def build_song_uris(
    user,
    song_list: list[str],
) -> list[str]:
    """
    Get the URIs for songs in a combined playlist.
    """
    song_uris = []
    for song in song_list:
        if Song.objects.filter(name__iexact=song).exists():
            song_uri = Song.objects.get(name__iexact=song).spotify_uri
        else:
            song_uri = get_spotify_song_uri(user, song)
            Song.objects.create(name=song, spotify_uri=song_uri)
        
        song_uris.append(song_uri)

    return song_uris