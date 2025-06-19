from django.contrib import admin
from .models import Playlist, Song

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('theme',)

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('name', 'spotify_uri')