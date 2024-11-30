from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SpotifyProfile, SpotifyWrap
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from django.conf import settings
import time  # For token expiration handling


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


@login_required
def generate_wrap(request):
    profile = SpotifyProfile.objects.get(user=request.user)

    # Check if access token is expired or expires_at is missing
    if is_token_expired(profile):
        refreshed = refresh_spotify_token(profile)
        if not refreshed:
            # Redirect to reauthenticate
            return redirect('spotify_connect')

    sp = Spotify(auth=profile.access_token)

    # Fetch user data from Spotify
    try:
        # Fetch top tracks - reduced limit due to API constraints
        top_tracks_data = sp.current_user_top_tracks(limit=5, time_range="medium_term")['items']

        # Fetch top artists - reduced limit
        top_artists_data = sp.current_user_top_artists(limit=5, time_range="medium_term")['items']

        # Recently played tracks
        recently_played_data = sp.current_user_recently_played(limit=10)['items']

        # Calculate basic listening stats
        total_tracks = len(top_tracks_data)

        # Prepare data for the wrap
        wrap_data = {
            "top_tracks": [
                {
                    "name": track['name'],
                    "artist": track['artists'][0]['name']
                } for track in top_tracks_data
            ],
            "top_artists": [
                {
                    "name": artist['name'],
                    "genres": artist.get('genres', [])[:2]  # Take first 2 genres
                } for artist in top_artists_data
            ],
            "recently_played": [
                {
                    "track": item['track']['name'],
                    "artist": item['track']['artists'][0]['name']
                } for item in recently_played_data
            ],
            "listening_stats": {
                "total_tracks_analyzed": total_tracks,
                "tracks_average_popularity": round(
                    sum(track.get('popularity', 0) for track in top_tracks_data) / total_tracks
                    if total_tracks > 0 else 0,
                    2
                )
            }
        }

        # Save the wrap data to the database
        wrap = SpotifyWrap(user=request.user, data=wrap_data)
        wrap.save()

    except SpotifyException as e:
        if e.http_status == 401:
            # Token is invalid or expired
            refreshed = refresh_spotify_token(profile)
            if refreshed:
                sp = Spotify(auth=profile.access_token)
                # Retry fetching data or redirect as needed
                return redirect('generate_wrap')  # Retry the view
            else:
                return redirect('spotify_connect')
        else:
            print(f"Spotify API error: {e}")
            return render(request, 'error.html')

    return render(request, 'wrap.html', {'wrap_data': wrap_data})


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