from django.db import models
from django.contrib.auth.models import User

class SpotifyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=50, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField(null=True, blank=True)  # Token expiry

    def __str__(self):
        return f"{self.user.username}'s Spotify Profile"

class SpotifyWrap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.JSONField()
    top_genre = models.CharField(max_length=255, blank=True, null=True)  # Field for top genre
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Spotify Wrap"
