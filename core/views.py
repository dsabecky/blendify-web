from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.blendify_utils import build_individual_playlist, build_combined_playlist, build_song_uris
from core.spotify_utils import get_spotify_playlists, update_spotify_playlist
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

@login_required
def blend(request):

    error = None
    spotify_playlists = get_spotify_playlists(request.user)

    # TODO: They've submitted something, so we process it.
    if request.method == 'POST':
        playlist_rename = request.POST.get('playlist_rename')

        # there's no playlist selected
        if not request.POST.get('spotify_playlist'):
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': 'Please select a playlist.',
            })
        
        # store the selected spotify playlist id and name
        spotify_playlist_id = request.POST.get('spotify_playlist')
        spotify_playlist_name = request.POST.get('spotify_playlist_name')

        # there's no themes entered
        if not request.POST.getlist('theme'):
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': 'Please enter at least one theme.',
            })
        
        # filter and sort our themes
        themes = [theme.strip() for theme in request.POST.getlist('theme') if theme.strip()]
        themes = sorted(themes)

        # not enough themes
        if not themes or len(themes) < 2:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': 'Please enter at least two themes.',
            })
        
        # build the individual playlists, or fail gracefully
        try:
            individual_playlists = {}
            for theme in themes:
                send_progress(request.user.id, f"Sourcing playlist for: {theme}")
                individual_playlists[theme] = build_individual_playlist(theme)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error building individual playlists: {e}',
            })
        
        print(individual_playlists)

        # build the combined playlist, or fail gracefully
        send_progress(request.user.id, "Building combined playlist")
        try:
            
            combined_playlist = build_combined_playlist(individual_playlists)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error building combined playlist: {e}',
            })

        # grab URIs for the songs in the combined playlist, or fail gracefully
        try:
            send_progress(request.user.id, "Adding song URIs to database...")
            song_uris = build_song_uris(request.user, combined_playlist)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error building song URIs: {e}',
            })
        
        # build a name for the playlist (if selected), or fail gracefully
        try:
            send_progress(request.user.id, "Creating a new playlist name...")
            playlist_name = build_playlist_name(combined_playlist, spotify_playlist_name, playlist_rename)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error building playlist name: {e}',
            })

        # build a description for the playlist (if selected), or fail gracefully
        try:
            send_progress(request.user.id, "Creating a new playlist description...")
            playlist_description = build_playlist_description(request.user, combined_playlist, spotify_playlist_id, playlist_rename)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error building playlist description: {e}',
            })

        # push the combined playlist to spotify
        try:
            send_progress(request.user.id, "Pushing new playlist to Spotify...")
            update_spotify_playlist(request.user, spotify_playlist_id, song_uris, playlist_name, playlist_description)
        except Exception as e:
            return render(request, 'blend.html', {
                'spotify_playlists': spotify_playlists,
                'error': f'Error updating playlist: {e}',
            })
        
        return render(request, 'blend.html', {
            'spotify_playlists': spotify_playlists,
            'playlist_name': playlist_name,
            'playlist_description': playlist_description,
            'combined_playlist': combined_playlist,
            'individual_playlists': individual_playlists,
            'success': 'Playlist updated successfully.',
        })
        
    
    # TODO: fresh load of the page    
    return render(request, 'blend.html', {
        'spotify_playlists': spotify_playlists,
    })









        
        

    return render(request, 'blend.html', {
        'spotify_playlists': spotify_playlists,
        'error': error,
    })

# @login_required
# def blend(request):
#     error = None
#     if request.method == 'POST':
#         action = request.POST.get('action')

#         if action == 'push':
#             selected_playlist_id = request.POST.get('spotify_playlist')


#         themes = [theme.strip() for theme in request.POST.getlist('theme') if theme.strip()]
#         spotify_playlists = get_spotify_playlists(request.user)
#         playlists = {}

#         for theme in themes:
#             existing = Playlist.objects.filter(theme__iexact=theme).first()

#             if existing:
#                 response_text = existing.playlist_text

#             else:
#                 conversation = chatgpt_playlist_prompt(theme)
#                 response_text = invoke_chatgpt(conversation)
#                 Playlist.objects.create(theme=theme, playlist_text=response_text)

#             playlists[theme] = response_text.splitlines() if response_text else []

#         return render(request, 'blend.html', {
#             'themes': themes,
#             'playlists': playlists,
#             'error': error,
#             'spotify_playlists': sorted(spotify_playlists, key=lambda x: x['name'].lower()),
#         })

#     return render(request, 'blend.html')