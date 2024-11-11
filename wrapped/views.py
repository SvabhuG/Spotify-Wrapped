from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import SpotifyProfile, SpotifyWrap
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
import json

sp_oauth = SpotifyOAuth(
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIFY_REDIRECT_URI,
    scope="user-top-read user-read-recently-played user-library-read"  # Updated scope
)


@login_required
def spotify_connect(request):
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@login_required
def spotify_callback(request):
    code = request.GET.get('code')
    token_info = sp_oauth.get_access_token(code)

    if token_info:
        sp = Spotify(auth=token_info['access_token'])
        spotify_id = sp.current_user()['id']

        profile, created = SpotifyProfile.objects.get_or_create(
            user=request.user,
            defaults={'spotify_id': spotify_id, 'access_token': token_info['access_token'],
                      'refresh_token': token_info['refresh_token']}
        )

        if not created:
            profile.access_token = token_info['access_token']
            profile.refresh_token = token_info['refresh_token']
            profile.save()

        return redirect('generate_wrap')

    return render(request, 'error.html')


@login_required
def generate_wrap(request):
    profile = SpotifyProfile.objects.get(user=request.user)
    sp = Spotify(auth=profile.access_token)

    # Fetch detailed data
    top_tracks = sp.current_user_top_tracks(limit=10, time_range="long_term")['items']
    top_artists = sp.current_user_top_artists(limit=5, time_range="long_term")['items']
    top_genres = list(set(genre for artist in top_artists for genre in artist['genres']))
    recently_played = sp.current_user_recently_played(limit=10)['items']

    # Create wrap data for display
    wrap_data = {
        "top_tracks": [{"name": track['name'], "artist": track['artists'][0]['name']} for track in top_tracks],
        "top_artists": [{"name": artist['name']} for artist in top_artists],
        "top_genres": top_genres,
        "recently_played": [{"track": item['track']['name'], "artist": item['track']['artists'][0]['name']} for item in
                            recently_played]
    }

    # Save the wrap in the database
    wrap = SpotifyWrap(user=request.user, data=wrap_data)
    wrap.save()

    return render(request, 'wrap.html', {'wrap_data': wrap_data})


@login_required
def wrap_history(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'wraps': wraps})

