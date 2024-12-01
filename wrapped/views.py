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
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-top-read user-read-recently-played",
        cache_path=None  # Disable cache file usage
    )

def is_token_expired(profile):
    if not profile.expires_at:
        # `expires_at` is missing; consider the token expired
        return True
    now = int(time.time())
    return profile.expires_at - now < 60  # Consider expired if less than 1 minute remains

def refresh_spotify_token(profile):
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
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@login_required
def spotify_callback(request):
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

from .spotify_api import get_user_top_artists, get_user_top_tracks, get_recently_played




@login_required
def generate_wrap(request):
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
        top_tracks = get_user_top_tracks(access_token)
        logging.debug(f"Fetched top tracks: {top_tracks}")

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

    except SpotifyException as e:
        logging.error(f"Spotify API Error: {e}")
        return redirect('spotify_connect')

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return redirect('spotify_connect')


@login_required
def wrap_history(request):
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
