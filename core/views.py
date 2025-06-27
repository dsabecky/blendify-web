from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.models import Generated

from core.blendify_utils import build_individual_playlists, build_combined_playlist, build_song_uris
from core.spotify_utils import create_spotify_playlist, get_spotify_playlists, update_spotify_access_token, update_spotify_playlist
from core.blendify_utils import build_playlist_name, build_playlist_description

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_progress(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_progress",
            "message": message,
        }
    )

def home(request):
    return render(request, 'home.html')

def lorumipsum(request):
    return render(request, 'lorumipsum.html')

def hathor(request):
    return render(request, 'hathor.html')

@login_required
def get_playlist_themes(request):
    playlist_name = request.GET.get('playlist_name')
    user_id = request.user.social_auth.filter(provider='spotify').first().uid

    generated = Generated.objects.filter(playlist_name=playlist_name, user_id=user_id).first()
    if generated:
        return JsonResponse({'themes': generated.themes})
    else:
        return JsonResponse({'themes': []})

@login_required
def blend(request):

    try: # get the users info from database
        social = request.user.social_auth.filter(provider='spotify').first()
    except Exception:
        return render(request, 'blend.html', { 'error': 'You are not authenticated with Spotify.' })

    try: # update the access token if it's expired
        update_spotify_access_token(request.user)
    except Exception as e:
        return render(request, 'blend.html', { 'error': f'Error updating Spotify access token: {e}' })
    
    access_token = social.extra_data['access_token']
    user_id = social.uid

    try: # get the user's spotify playlists
        spotify_playlists = get_spotify_playlists(access_token, user_id)
    except Exception as e:
        return render(request, 'blend.html', { 'error': f'Error getting Spotify playlists: {e}' })

    if request.method == 'POST': # they've submitted something, so we process it
        playlist_rename = request.POST.get('playlist_rename')

        if not request.POST.get('spotify_playlist'): # there's no playlist selected
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': 'Please select a playlist.' })
        
        spotify_playlist_id = request.POST.get('spotify_playlist')
        spotify_playlist_name = request.POST.get('spotify_playlist_name')

        if not request.POST.getlist('theme'): # there's no themes entered
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': 'Please enter at least one theme.' })
        
        # filter and sort our themes
        themes = [theme.strip() for theme in request.POST.getlist('theme') if theme.strip()]
        themes = sorted(themes)

        if not themes or len(themes) < 2: # not enough themes
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': 'Please enter at least two themes.' })
        
        if spotify_playlist_id == 'create_new': # we're creating a new playlist
            new_playlist_name = request.POST.get('new_playlist_name', '').strip()

            if not new_playlist_name: # no name entered
                return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': 'Please enter a name for the new playlist.' })
            
            try: # create the new playlist
                spotify_playlist_id = create_spotify_playlist(access_token, user_id, new_playlist_name)
                spotify_playlist_name = new_playlist_name
            except Exception as e:
                return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error creating new playlist: {e}' })
        
        try: # build the individual playlists
            send_progress(request.user.id, "Sourcing playlists for:<br>" + "<br>".join([f" {i+1}. {theme}" for i, theme in enumerate(themes)]))
            individual_playlists = build_individual_playlists(themes)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error building individual playlists: {e}' })

        try:# build the combined playlist
            send_progress(request.user.id, "Building combined playlist")
            combined_playlist = build_combined_playlist(individual_playlists)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error building combined playlist: {e}' })

        try: # grab URIs for the songs in the combined playlist
            send_progress(request.user.id, "Adding song URIs to database...")
            song_uris = build_song_uris(access_token, combined_playlist)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error building song URIs: {e}' })
        
        try: # build a name for the playlist (if selected)
            send_progress(request.user.id, "Creating a new playlist name...")
            playlist_name = build_playlist_name(combined_playlist, spotify_playlist_name, playlist_rename)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error building playlist name: {e}' })

        try: # build a description for the playlist (if selected)
            send_progress(request.user.id, "Creating a new playlist description...")
            playlist_description = build_playlist_description(access_token, combined_playlist, spotify_playlist_id, playlist_rename)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error building playlist description: {e}' })

        try: # push the combined playlist to spotify
            send_progress(request.user.id, "Pushing new playlist to Spotify...")
            update_spotify_playlist(access_token, spotify_playlist_id, song_uris, playlist_name, playlist_description)
        except Exception as e:
            return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists, 'error': f'Error updating playlist: {e}' })
        
        Generated.objects.update_or_create(playlist_name=playlist_name, user_id=user_id, defaults={'themes': themes})
        
        # great success, return the results
        return render(request, 'blend.html', {
            'spotify_playlists': spotify_playlists,
            'playlist_name': playlist_name,
            'playlist_description': playlist_description,
            'combined_playlist': combined_playlist,
            'individual_playlists': individual_playlists,
            'success': 'Playlist updated successfully.',
        })
        
    # fresh load of the page    
    return render(request, 'blend.html', { 'spotify_playlists': spotify_playlists })