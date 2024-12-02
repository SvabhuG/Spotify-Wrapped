from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
import time
import requests
import logging
from urllib.parse import urlencode
from .models import SpotifyProfile, SpotifyWrap
from .spotify_api import (
    get_user_followed_artists,
    get_user_top_artists,
    get_user_top_tracks,
    get_recently_played,
)


def is_token_expired(profile):
    """
        Check if the access token for a given profile is expired or about to expire.

        Args:
            profile (SpotifyProfile): The profile object containing the access token and its expiration time.

        Returns:
            bool: True if the token is expired or will expire in less than 60 seconds; False otherwise.
        """

    if not profile.expires_at:
        # `expires_at` is missing; consider the token expired
        return True
    now = int(time.time())
    return profile.expires_at - now < 60  # Consider expired if less than 1 minute remains


def refresh_spotify_token(profile):
    """
        Refresh the access token for a given Spotify profile using the refresh token.

        Args:
            profile (SpotifyProfile): The profile object containing the current refresh token and other details.

        Returns:
            bool: True if the token was successfully refreshed; False otherwise.
        """

    token_url = "https://accounts.spotify.com/api/token"
    client_id = settings.SPOTIPY_CLIENT_ID
    client_secret = settings.SPOTIPY_CLIENT_SECRET

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': profile.refresh_token,
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    auth = (client_id, client_secret)

    response = requests.post(token_url, data=data, headers=headers, auth=auth)
    if response.status_code != 200:
        print("Error refreshing token:", response.text)
        return False

    token_info = response.json()
    profile.access_token = token_info['access_token']
    if 'refresh_token' in token_info:
        profile.refresh_token = token_info['refresh_token']
    expires_in = token_info.get('expires_in')
    profile.expires_at = int(time.time()) + expires_in
    profile.save()
    return True


@login_required
def spotify_connect(request):
    """
        Redirect the user to Spotify's authorization page for user authentication and consent.

        Args:
            request (HttpRequest): The HTTP request object containing user and request data.

        Returns:
            HttpResponse: A redirect response to Spotify's authorization page.
        """

    client_id = settings.SPOTIPY_CLIENT_ID
    redirect_uri = settings.SPOTIPY_REDIRECT_URI
    scope = "user-top-read user-read-recently-played user-follow-read"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return redirect(auth_url)


@login_required
def spotify_callback(request):
    """
        Handle the callback from Spotify after user authentication and obtain the access and refresh tokens.

        Args:
            request (HttpRequest): The HTTP request object containing the callback data from Spotify.

        Returns:
            HttpResponse: Redirect response to the 'generate_wrap' page if successful, or an error page if not.
        """

    code = request.GET.get('code')
    if not code:
        return render(request, 'error.html', {'message': 'No code provided in the callback.'})

    token_url = "https://accounts.spotify.com/api/token"
    redirect_uri = settings.SPOTIPY_REDIRECT_URI
    client_id = settings.SPOTIPY_CLIENT_ID
    client_secret = settings.SPOTIPY_CLIENT_SECRET

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    auth = (client_id, client_secret)

    response = requests.post(token_url, data=data, headers=headers, auth=auth)
    if response.status_code != 200:
        print("Failed to obtain token_info. Response:", response.text)
        return render(request, 'error.html', {'message': 'Failed to obtain token information from Spotify.'})

    token_info = response.json()
    print("Received token_info:", token_info)

    if token_info:
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in')
        expires_at = int(time.time()) + expires_in

        # Use the access token to get user profile
        user_profile_url = "https://api.spotify.com/v1/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(user_profile_url, headers=headers)
        if response.status_code != 200:
            print("Failed to get user profile. Response:", response.text)
            return render(request, 'error.html', {'message': 'Failed to get user profile from Spotify.'})

        spotify_user = response.json()
        spotify_id = spotify_user['id']
        print("Authenticated Spotify user ID:", spotify_id)

        try:
            # Check if a SpotifyProfile with this spotify_id already exists
            profile = SpotifyProfile.objects.get(spotify_id=spotify_id)
            if profile.user != request.user:
                # The Spotify account is already linked to another user
                print("Spotify account is already linked to another user.")
                return render(request, 'error.html', {
                    'message': 'This Spotify account is already linked to another user.'
                })
            else:
                # Update the existing profile
                print("Updating existing SpotifyProfile for the same user.")
                profile.access_token = access_token
                profile.refresh_token = refresh_token
                profile.expires_at = expires_at
                profile.save()
                print("SpotifyProfile updated successfully.")
        except SpotifyProfile.DoesNotExist:
            # Create a new profile
            print("Creating new SpotifyProfile.")
            profile = SpotifyProfile.objects.create(
                user=request.user,
                spotify_id=spotify_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            print("SpotifyProfile created successfully.")

        return redirect('generate_wrap')

    print("Failed to obtain token_info.")
    return render(request, 'error.html', {'message': 'Failed to obtain token information from Spotify.'})


@login_required
def generate_wrap(request):
    """
        Generate and display a personalized Spotify wrap for the authenticated user.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: Renders the 'wrap.html' template with wrap data or redirects to the Spotify connection page if an error occurs.
        """

    logging.debug("Starting generate_wrap method")

    # Get access token
    profile = SpotifyProfile.objects.filter(user=request.user).first()
    if not profile:
        logging.warning("No Spotify profile found for the user")
        return redirect('spotify_connect')

    # Refresh token if needed
    if is_token_expired(profile):
        logging.info("Access token expired. Attempting to refresh.")
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            logging.error("Failed to refresh token. Redirecting to Spotify connect.")
            return redirect('spotify_connect')

    access_token = profile.access_token
    logging.debug("Access token acquired successfully")

    try:
        # Fetch user profile
        user_profile_url = "https://api.spotify.com/v1/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(user_profile_url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to get user profile. Response: {response.text}")
            return redirect('spotify_connect')

        user_profile = response.json()
        spotify_username = user_profile.get('display_name', 'Spotify User')
        logging.debug(f"Fetched Spotify user profile: {spotify_username}")

        # Fetch top artists
        top_artists_raw = get_user_top_artists(access_token)
        logging.debug(f"Raw top artists data: {top_artists_raw}")
        top_artists = [
            {
                'name': artist['name'],
                'profile_pic': artist['images'][0]['url'] if artist.get('images') else None
            }
            for artist in top_artists_raw
        ]
        logging.debug(f"Processed top artists data: {top_artists}")

        # Fetch top tracks
        top_tracks_raw = get_user_top_tracks(access_token)
        logging.debug(f"Raw top tracks data: {top_tracks_raw}")
        top_tracks = [
            {
                'name': track['name'],
                'artist': ', '.join(artist['name'] for artist in track['artists']),
                'album_name': track['album']['name'],
                'album_cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
            }
            for track in top_tracks_raw
        ]
        logging.debug(f"Processed top tracks data: {top_tracks}")

        # Process recently played tracks
        recently_played_raw = get_recently_played(access_token)
        logging.debug(f"Raw recently played data: {recently_played_raw}")

        # Handle recently_played_raw depending on its type
        if isinstance(recently_played_raw, dict):
            recently_played_items = recently_played_raw.get('items', [])
        elif isinstance(recently_played_raw, list):
            recently_played_items = recently_played_raw
        else:
            recently_played_items = []

        logging.debug(f"Processed recently played items: {recently_played_items}")

        # Extract track details
        recently_played = [
            {
                'track': item['track']['name'],
                'artist': ', '.join(artist['name'] for artist in item['track']['artists']),
                'album_name': item['track']['album']['name'],
                'album_cover': item['track']['album']['images'][0]['url']
                if item['track']['album']['images'] else None,
                'played_at': item['played_at'],
            }
            for item in recently_played_items
        ]
        logging.debug(f"Processed recently played tracks: {recently_played}")

        # Fetch followed artists
        followed_artists = get_user_followed_artists(access_token)
        logging.debug(f"Fetched followed artists: {followed_artists}")

        # Prepare wrap data
        wrap_data = {
            'spotify_username': spotify_username,
            'top_artists': top_artists,
            'top_tracks': top_tracks,
            'recently_played': recently_played,
            'followed_artists': followed_artists,
        }
        logging.info(f"Wrap data prepared successfully: {wrap_data}")

        # Save wrap to the database
        SpotifyWrap.objects.create(
            user=request.user,
            data=wrap_data  # Ensure data is JSON-serializable
        )
        logging.info("Wrap data saved to the database successfully")

        # Pass data to the template
        return render(request, 'wrap.html', {'wrap_data': wrap_data})

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return redirect('spotify_connect')


@login_required
def wrap_history(request):
    """
        Display the history of Spotify wraps for the authenticated user.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: Renders the 'history.html' template with wrap history or redirects to the Spotify connection page if the user is not authenticated or has issues with the access token.
        """

    profile = SpotifyProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('spotify_connect')

    # Check if access token is expired or expires_at is missing
    if is_token_expired(profile):
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            return redirect('spotify_connect')

    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'wraps': wraps})


@login_required
def replay_wrap(request, wrap_id):
    """
        Display a specific wrap from the user's wrap history.

        Args:
            request (HttpRequest): The HTTP request object.
            wrap_id (int): The ID of the specific wrap to be displayed.

        Returns:
            HttpResponse: Renders the 'wrap.html' template with the specified wrap data or redirects to the Spotify connection page if the user is not authenticated or has issues with the access token.
        """

    profile = SpotifyProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('spotify_connect')

    # Check if access token is expired or expires_at is missing
    if is_token_expired(profile):
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            return redirect('spotify_connect')

    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    wrap_data = wrap.data
    return render(request, 'wrap.html', {'wrap_data': wrap_data})