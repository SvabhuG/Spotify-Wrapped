from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SpotifyProfile, SpotifyWrap
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from datetime import timedelta
import time

# Configure SpotifyOAuth for authentication and data access
sp_oauth = SpotifyOAuth(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIPY_REDIRECT_URI,
    scope="user-top-read user-read-recently-played user-library-read user-read-playback-position"
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

        # Save or update the user's Spotify profile
        profile, created = SpotifyProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'spotify_id': spotify_id,
                'access_token': token_info['access_token'],
                'refresh_token': token_info['refresh_token']
            }
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

    # Fetch user data from Spotify
    top_tracks_data = sp.current_user_top_tracks(limit=10, time_range="long_term")['items']
    top_artists_data = sp.current_user_top_artists(limit=5, time_range="long_term")['items']
    top_genres = list(set(genre for artist in top_artists_data for genre in artist['genres']))
    recently_played_data = sp.current_user_recently_played(limit=10)['items']

    # Fetch favorite album
    favorite_albums = sp.current_user_saved_albums(limit=50)['items']
    album_play_counts = {}

    for album_item in favorite_albums:
        album = album_item['album']
        album_tracks = album['tracks']['items']
        play_count = 0
        for track in album_tracks:
            track_id = track['id']
            # Assume we have a way to get play count per track (Note: Spotify API does not provide this directly)
            # For demo purposes, we'll simulate play counts
            play_count += 1  # Replace with actual play count retrieval if possible
        album_play_counts[album['id']] = {
            'name': album['name'],
            'artist': album['artists'][0]['name'],
            'play_count': play_count
        }

    # Find the album with the highest play count
    favorite_album = max(album_play_counts.values(), key=lambda x: x['play_count']) if album_play_counts else None

    # Calculate listening habits
    total_minutes = 0
    total_tracks = 0
    total_duration_ms = 0

    all_tracks = sp.current_user_top_tracks(limit=50, time_range="long_term")['items']
    for track in all_tracks:
        total_tracks += 1
        total_duration_ms += track['duration_ms']

    total_minutes = int(total_duration_ms / (1000 * 60))
    average_song_duration = round((total_duration_ms / total_tracks) / (1000 * 60), 2) if total_tracks > 0 else 0

    # Get audio features
    track_ids = [track['id'] for track in all_tracks]
    audio_features_list = sp.audio_features(tracks=track_ids)
    energy = danceability = acousticness = valence = 0
    feature_count = 0

    for features in audio_features_list:
        if features:
            energy += features['energy']
            danceability += features['danceability']
            acousticness += features['acousticness']
            valence += features['valence']
            feature_count += 1

    if feature_count > 0:
        energy = int((energy / feature_count) * 100)
        danceability = int((danceability / feature_count) * 100)
        acousticness = int((acousticness / feature_count) * 100)
        valence = int((valence / feature_count) * 100)
    else:
        energy = danceability = acousticness = valence = 0

    # Fetch top podcasts
    top_podcasts_data = sp.current_user_saved_shows(limit=5)['items']
    top_podcasts = []
    for item in top_podcasts_data:
        show = item['show']
        episodes_listened = 0  # Since Spotify API does not provide this, we can simulate or omit
        top_podcasts.append({
            'name': show['name'],
            'episodes_listened': episodes_listened  # Replace with actual data if available
        })

    # Prepare data for the wrap
    wrap_data = {
        "top_tracks": [{"name": track['name'], "artist": track['artists'][0]['name']} for track in top_tracks_data],
        "top_artists": [{"name": artist['name']} for artist in top_artists_data],
        "top_genres": top_genres,
        "recently_played": [
            {"track": item['track']['name'], "artist": item['track']['artists'][0]['name']}
            for item in recently_played_data
        ],
        "favorite_album": favorite_album,
        "total_minutes": total_minutes,
        "total_tracks": total_tracks,
        "average_song_duration": average_song_duration,
        "audio_features": {
            "energy": energy,
            "danceability": danceability,
            "acousticness": acousticness,
            "valence": valence
        },
        "top_podcasts": top_podcasts
    }

    # Save the wrap data to the database
    wrap = SpotifyWrap(user=request.user, data=wrap_data)
    wrap.save()

    return render(request, 'wrap.html', {'wrap_data': wrap_data})

@login_required
def wrap_history(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'wraps': wraps})

@login_required
def replay_wrap(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    wrap_data = wrap.data  # Access the saved wrap data
    return render(request, 'wrap.html', {'wrap_data': wrap_data})
