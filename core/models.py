from django.db import models

class Playlist(models.Model):
    theme = models.CharField(max_length=255)
    song_list = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.theme
    
class Song(models.Model):
    name = models.CharField(max_length=255)
    spotify_uri = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.spotify_uri})"