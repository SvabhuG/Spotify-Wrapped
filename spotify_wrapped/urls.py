"""
URL configuration for spotify_wrapped project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from wrapped import views  # Import views from the wraps app

urlpatterns = [
    path('account/', include('allauth.urls')),  # For user authentication
    path('wraps/connect/', views.spotify_connect, name='spotify_connect'),  # Connect to Spotify
    path('wraps/callback/', views.spotify_callback, name='spotify_callback'),  # Handle Spotify callback
    path('wraps/generate/', views.generate_wrap, name='generate_wrap'),  # Generate new wrap
    path('wraps/history/', views.wrap_history, name='wrap_history'),  # View wrap history
    path('wraps/replay/<int:wrap_id>/', views.replay_wrap, name='replay_wrap'),  # Replay a saved wrap
]

