from django.db import models
from social_django.models import UserSocialAuth

# Add fields directly to the existing UserSocialAuth model
UserSocialAuth.add_to_class('spotify_user_id', models.CharField(max_length=255, blank=True, null=True))
UserSocialAuth.add_to_class('spotify_access_token', models.TextField(blank=True, null=True))
UserSocialAuth.add_to_class('spotify_refresh_token', models.TextField(blank=True, null=True))

class Playlist(models.Model):
    theme = models.CharField(max_length=255, db_index=True)
    song_list = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['theme']),
            models.Index(models.functions.Lower('theme'), name='playlist_theme_lower_idx'),
        ]

    def __str__(self):
        return self.theme
    
class Song(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    spotify_uri = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(models.functions.Lower('name'), name='song_name_lower_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('name'), 
                name='unique_song_name_case_insensitive'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.spotify_uri})"