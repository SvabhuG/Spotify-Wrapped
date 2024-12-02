from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import SpotifyProfile, SpotifyWrap
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from django.conf import settings
from collections import Counter
import time
import requests
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import SpotifyWrap, SpotifyProfile
from .spotify_api import (
    get_user_top_artists,
    get_user_top_tracks,
    get_recently_played,
    get_user_followed_artists,  # Import the new function
)

def get_spotify_oauth():
    """
    Create and return a SpotifyOAuth object for handling Spotify authentication.
    """
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-top-read user-read-recently-played",
        cache_path=None  # Disable cache file usage
    )

def is_token_expired(profile):
    """
    Check if the Spotify access token for the given profile is expired.

    Args:
        profile (SpotifyProfile): The user's Spotify profile.

    Returns:
        bool: True if the token is expired or will expire in less than 60 seconds, False otherwise.
    """
    if not profile.expires_at:
        # `expires_at` is missing; consider the token expired
        return True
    now = int(time.time())
    return profile.expires_at - now < 60  # Consider expired if less than 1 minute remains

def refresh_spotify_token(profile):
    """
    Refresh the Spotify access token for the given profile.

    Args:
        profile (SpotifyProfile): The user's Spotify profile.

    Returns:
        bool: True if the token was successfully refreshed, False otherwise.
    """
    sp_oauth = get_spotify_oauth()
    try:
        token_info = sp_oauth.refresh_access_token(profile.refresh_token)
        profile.access_token = token_info['access_token']
        if 'refresh_token' in token_info:
            profile.refresh_token = token_info['refresh_token']
        profile.expires_at = token_info['expires_at']
        profile.save()
        return True
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return False

@login_required
def spotify_connect(request):
    """
    Redirect the user to the Spotify authorization page to initiate the connection process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A redirect response to the Spotify authorization page.
    """
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@login_required
def spotify_callback(request):
    """
    Handle the callback from Spotify after user authentication, and store the user's tokens.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A redirect response to either the 'generate_wrap' view or an error page.
    """
    code = request.GET.get('code')
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    print("Received token_info:", token_info)

    if token_info:
        sp = Spotify(auth=token_info['access_token'])
        spotify_user = sp.current_user()
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
                profile.access_token = token_info['access_token']
                profile.refresh_token = token_info['refresh_token']
                profile.expires_at = token_info['expires_at']
                profile.save()
                print("SpotifyProfile updated successfully.")
        except SpotifyProfile.DoesNotExist:
            # Create a new profile
            print("Creating new SpotifyProfile.")
            profile = SpotifyProfile.objects.create(
                user=request.user,
                spotify_id=spotify_id,
                access_token=token_info['access_token'],
                refresh_token=token_info['refresh_token'],
                expires_at=token_info['expires_at']
            )
            print("SpotifyProfile created successfully.")

        return redirect('generate_wrap')

    print("Failed to obtain token_info.")
    return render(request, 'error.html', {'message': 'Failed to obtain token information from Spotify.'})

def followed_artists(request):
    """
    Retrieve the list of artists followed by the authenticated user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response containing the followed artists or an error message.
    """
    access_token = request.session.get("access_token")  # Retrieve stored token

    if not access_token:
        return JsonResponse({"error": "User is not authenticated."}, status=401)

    url = "https://api.spotify.com/v1/me/following"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"type": "artist", "limit": 20}

    # Make API request
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        followed_artists = response.json()
        return JsonResponse(followed_artists)  # Return data as JSON response
    else:
        return JsonResponse(
            {"error": "Failed to fetch followed artists", "details": response.json()},
            status=response.status_code,
        )

@login_required
def generate_wrap(request):
    """
    Generate a Spotify Wrapped summary for the authenticated user and store it in the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response rendering the 'wrap.html' template with the user's wrap data.
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

    # Create Spotify client
    sp = Spotify(auth=access_token)

    try:
        # Fetch user profile
        user_profile = sp.current_user()
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
        logging.debug(f"Fetched followed artists data: {followed_artists}")

        # Create a summary of artist counts
        artist_names = [artist['name'] for artist in followed_artists]
        artist_counts = Counter(artist_names)
        artist_summary = artist_counts.most_common(5)  # Get the top 5 followed artists

        logging.debug(f"Top followed artists summary: {artist_summary}")

        # Save wrap data to the database
        wrap = SpotifyWrap(
            user=request.user,
            top_artists=top_artists,
            top_tracks=top_tracks,
            recently_played=recently_played,
            followed_artists=artist_summary,
        )
        wrap.save()

        logging.info("SpotifyWrap data saved successfully")

        return render(
            request,
            "wrap.html",
            {
                "spotify_username": spotify_username,
                "top_artists": top_artists,
                "top_tracks": top_tracks,
                "recently_played": recently_played,
                "followed_artists": artist_summary,
            },
        )
    except SpotifyException as e:
        logging.error(f"SpotifyException occurred: {e}")
        return render(request, 'error.html', {'message': 'An error occurred while fetching data from Spotify.'})
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return render(request, 'error.html', {'message': 'An unexpected error occurred.'})

@login_required
def wrap_history(request):
    """
    Display the history of Spotify Wrapped summaries for the authenticated user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response rendering the 'history.html' template with the user's wrap history.
    """
    profile = SpotifyProfile.objects.filter(user=request.user).first()
    if not profile:
        # Redirect to Spotify connection if no profile exists for the user
        return redirect('spotify_connect')

    # Check if the access token is expired or if the expiration time is missing
    if is_token_expired(profile):
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            # Redirect to Spotify connection if the token refresh fails
            return redirect('spotify_connect')

    # Fetch the user's Spotify Wrap history and order by creation date
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'wraps': wraps})

@login_required
def replay_wrap(request, wrap_id):
    """
    Display a specific Spotify Wrapped summary for the authenticated user.

    Args:
        request (HttpRequest): The HTTP request object.
        wrap_id (int): The ID of the wrap to display.

    Returns:
        HttpResponse: A response rendering the 'wrap.html' template with the wrap data.
    """
    profile = SpotifyProfile.objects.filter(user=request.user).first()
    if not profile:
        # Redirect to Spotify connection if no profile exists for the user
        return redirect('spotify_connect')

    # Check if the access token is expired or if the expiration time is missing
    if is_token_expired(profile):
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            # Redirect to Spotify connection if the token refresh fails
            return redirect('spotify_connect')

    # Retrieve the specific wrap object, or return a 404 if not found
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    wrap_data = wrap.data  # Extract the wrap data from the object

    return render(request, 'wrap.html', {'wrap_data': wrap_data})
