import requests

BASE_URL = "https://api.spotify.com/v1/me"

def get_user_top_artists(access_token):
    """
    Fetch the user's top artists from Spotify.

    Args:
        access_token (str): The OAuth access token for the Spotify API.

    Returns:
        list: A list of dictionaries containing information about the user's top artists.
              Returns an empty list if the request fails.
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
    Fetch the user's top tracks from Spotify.

    Args:
        access_token (str): The OAuth access token for the Spotify API.

    Returns:
        list: A list of dictionaries containing information about the user's top tracks.
              Returns an empty list if the request fails.
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
    Fetch the user's recently played tracks from Spotify.

    Args:
        access_token (str): The OAuth access token for the Spotify API.

    Returns:
        list: A list of dictionaries containing information about the user's recently played tracks.
              Returns an empty list if the request fails.
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
    Fetch the artists followed by the user on Spotify.

    Args:
        access_token (str): The OAuth access token for the Spotify API.

    Returns:
        list: A list of dictionaries containing information about the user's followed artists.
              Returns an empty list if the request fails.
    """
    url = f"{BASE_URL}/following?type=artist&limit=10"  # Adjust the limit to 10 followed artists
    headers =
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['artists']['items']  # Returns a list of followed artists
    else:
        return []
