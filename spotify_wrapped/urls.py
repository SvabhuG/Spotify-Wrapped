# urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from wrapped import views  # Import views from the wrapped app
from django.views.generic import RedirectView

urlpatterns = [
    # Non-localized URLs can go here
    path('i18n/', include('django.conf.urls.i18n')),  # For language switching
]

urlpatterns += i18n_patterns(
    # Root URL mapping - redirect to login page
    path('', RedirectView.as_view(pattern_name='account_login', permanent=False), name='home'),

    # Application URLs
    path('account/', include('allauth.urls')),  # For user authentication

    path('wraps/connect/', views.spotify_connect, name='spotify_connect'),  # Connect to Spotify
    path('wraps/callback/', views.spotify_callback, name='spotify_callback'),  # Handle Spotify callback
    path('wraps/generate/', views.generate_wrap, name='generate_wrap'),  # Generate new wrap
    path('wraps/history/', views.wrap_history, name='wrap_history'),  # View wrap history
    path('wraps/replay/<int:wrap_id>/', views.replay_wrap, name='replay_wrap'),  # Replay a saved wrap

    # Admin URL
    path('admin/', admin.site.urls),
)
