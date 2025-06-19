# core/admin.py
from django.contrib import admin
from social_django.admin import UserSocialAuthOption
from social_django.models import UserSocialAuth
from .models import Playlist, Song

# Unregister the default admin
admin.site.unregister(UserSocialAuth)

# Register with custom admin that includes extended fields
@admin.register(UserSocialAuth)
class CustomUserSocialAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'uid', 'spotify_user_id', 'created')
    list_filter = ('provider', 'created')
    search_fields = ('user__username', 'uid', 'spotify_user_id')
    readonly_fields = ('created', 'modified')
    
    fieldsets = (
        ('Social Auth Info', {
            'fields': ('user', 'provider', 'uid', 'extra_data')
        }),
        ('Spotify Data', {
            'fields': ('spotify_user_id', 'spotify_access_token', 'spotify_refresh_token')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('theme',)

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('name', 'spotify_uri')