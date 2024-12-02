import requests

BASE_URL = "https://api.spotify.com/v1/me"

# Function to get top artists
def get_user_top_artists(access_token):
    """
        Fetch the top 10 artists for a user from the Spotify API.

        Args:
            access_token (str): The access token used for authenticating the request.

        Returns:
            list: A list of top artist objects if the request is successful; otherwise, an empty list.
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

# Function to get top tracks
def get_user_top_tracks(access_token):
    """
        Fetch the top 10 tracks for a user from the Spotify API.

        Args:
            access_token (str): The access token used for authenticating the request.

        Returns:
            list: A list of top track objects if the request is successful; otherwise, an empty list.
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

# Function to get recently played tracks
def get_recently_played(access_token):
    """
        Fetch the 10 most recently played tracks for a user from the Spotify API.

        Args:
            access_token (str): The access token used for authenticating the request.

        Returns:
            list: A list of recently played track objects if the request is successful; otherwise, an empty list.
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

# Function to get followed artists (NEW FUNCTION)
def get_user_followed_artists(access_token):
    """
        Fetch the 10 most recently followed artists for a user from the Spotify API.

        Args:
            access_token (str): The access token used for authenticating the request.

        Returns:
            list: A list of followed artist objects if the request is successful; otherwise, an empty list.
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