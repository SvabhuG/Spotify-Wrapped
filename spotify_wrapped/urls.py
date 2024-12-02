# your_project/urls.py

"""
URL Configuration for the Spotify Wrapped Project.

This module defines the URL routing for the entire Django project,
including internationalization support and application-specific routes.

Key Routing Components:
- User authentication routes
- Spotify connection and wrap generation routes
- Admin interface
- Internationalization support
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from wrapped import views  # Import views from the wrapped app
from django.views.generic import RedirectView

# Non-localized URL patterns
urlpatterns = [
    # Support for language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    # Root URL - Redirects to login page by default
    path('', RedirectView.as_view(pattern_name='account_login', permanent=False), name='home'),

    # Authentication Routes
    # Leverages django-allauth for comprehensive authentication management
    path('account/', include('allauth.urls')),

    # Spotify Wrap Generation Routes
    # Handles Spotify connection, callback, wrap generation, and history
    path('wraps/connect/', views.spotify_connect, name='spotify_connect'),  # Initiate Spotify OAuth
    path('wraps/callback/', views.spotify_callback, name='spotify_callback'),  # Handle OAuth callback
    path('wraps/generate/', views.generate_wrap, name='generate_wrap'),  # Create new Spotify Wrap
    path('wraps/history/', views.wrap_history, name='wrap_history'),  # View previous Wraps
    path('wraps/replay/<int:wrap_id>/', views.replay_wrap, name='replay_wrap'),  # Replay a specific Wrap

    # Django Admin Interface
    path('admin/', admin.site.urls),
)