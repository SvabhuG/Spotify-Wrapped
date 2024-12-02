from django.db import models
from django.contrib.auth.models import User

class SpotifyProfile(models.Model):
    """
    Represents a user's Spotify profile linked to their Django user account.

    Attributes:
        user (User): A one-to-one relationship with the Django User model.
        spotify_id (str): The unique identifier for the user on Spotify.
        access_token (str): The OAuth access token for accessing Spotify APIs.
        refresh_token (str): The OAuth refresh token for renewing the access token.
        expires_at (int): The timestamp indicating when the access token expires.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=50, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField(null=True, blank=True)  # Token expiry

    def __str__(self):
        """
        Returns a string representation of the Spotify profile.

        Returns:
            str: The username of the associated user with the suffix 'Spotify Profile'.
        """
        return f"{self.user.username}'s Spotify Profile"


class SpotifyWrap(models.Model):
    """
    Represents a generated Spotify Wrapped session for a user.

    Attributes:
        user (User): A foreign key relationship to the Django User model.
        data (JSONField): A JSON field storing the details of the Spotify Wrapped session.
        top_genre (str): The user's top genre for the session (optional).
        created_at (datetime): The timestamp when the Spotify Wrapped session was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.JSONField()
    top_genre = models.CharField(max_length=255, blank=True, null=True)  # Field for top genre
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the Spotify Wrapped session.

        Returns:
            str: The username of the associated user with the suffix 'Spotify Wrap'.
        """
        return f"{self.user.username}'s Spotify Wrap"
