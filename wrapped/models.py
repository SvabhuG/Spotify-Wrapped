from django.db import models
from django.contrib.auth.models import User

class SpotifyProfile(models.Model):
    """
    Represents a user's Spotify authentication profile.

    This model stores Spotify-specific authentication and user information,
    linking a Django user with their Spotify account credentials.

    Attributes:
        user (OneToOneField): One-to-one relationship with Django's User model.
        spotify_id (CharField): Unique Spotify user identifier.
        access_token (TextField): Current OAuth access token for Spotify API.
        refresh_token (TextField): Token used to obtain new access tokens.
        expires_at (IntegerField): Timestamp when the current access token expires.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=50, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField(null=True, blank=True)  # Token expiry

    def __str__(self):
        """
        String representation of the SpotifyProfile.

        Returns:
            str: Username's Spotify Profile
        """
        return f"{self.user.username}'s Spotify Profile"

class SpotifyWrap(models.Model):
    """
    Represents a user's Spotify Wrap, capturing their music listening data.

    This model stores a snapshot of a user's Spotify listening history,
    including top tracks, artists, and other music-related insights.

    Attributes:
        user (ForeignKey): Relationship to the Django User who created this Wrap.
        data (JSONField): Comprehensive JSON data of the Spotify Wrap.
        top_genre (CharField): Optional field to store the user's top music genre.
        created_at (DateTimeField): Timestamp of when the Wrap was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.JSONField()
    top_genre = models.CharField(max_length=255, blank=True, null=True)  # Field for top genre
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        String representation of the SpotifyWrap.

        Returns:
            str: Username's Spotify Wrap
        """
        return f"{self.user.username}'s Spotify Wrap"