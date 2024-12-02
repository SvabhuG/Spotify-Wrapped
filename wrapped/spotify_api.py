import requests

BASE_URL = "https://api.spotify.com/v1/me"

def get_user_top_artists(access_token):
    """
    Retrieve the user's top artists from Spotify.

    This function fetches the top 10 artists based on the user's listening history.

    Args:
        access_token (str): Spotify OAuth access token for authentication.

    Returns:
        list: A list of top artists. Returns an empty list if the request fails.
              Each artist is represented by a dictionary of artist details.
    """
    url = f"{BASE_URL}/top/artists?limit=10"  # Adjust the limit to 10 artists
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']  # Returns a list of top artists
    else:
        return []

def get_user_top_tracks(access_token):
    """
    Retrieve the user's top tracks from Spotify.

    This function fetches the top 10 tracks based on the user's listening history.

    Args:
        access_token (str): Spotify OAuth access token for authentication.

    Returns:
        list: A list of top tracks. Returns an empty list if the request fails.
              Each track is represented by a dictionary of track details.
    """
    url = f"{BASE_URL}/top/tracks?limit=10"  # Adjust the limit to 10 tracks
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']  # Returns a list of top tracks
    else:
        return []

def get_recently_played(access_token):
    """
    Retrieve the user's recently played tracks from Spotify.

    This function fetches the 10 most recently played tracks.

    Args:
        access_token (str): Spotify OAuth access token for authentication.

    Returns:
        list: A list of recently played tracks. Returns an empty list if the request fails.
              Each track is represented by a dictionary of track and play details.
    """
    url = f"{BASE_URL}/player/recently-played?limit=10"  # Adjust the limit to 10 tracks
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']  # Returns a list of recently played tracks
    else:
        return []

def get_user_followed_artists(access_token):
    """
    Retrieve the user's followed artists from Spotify.

    This function fetches the 10 most recently followed artists.

    Args:
        access_token (str): Spotify OAuth access token for authentication.

    Returns:
        list: A list of followed artists. Returns an empty list if the request fails.
              Each artist is represented by a dictionary of artist details.
    """
    url = f"{BASE_URL}/following?type=artist&limit=10"  # Adjust the limit to 10 followed artists
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['artists']['items']  # Returns a list of followed artists
    else:
        return []