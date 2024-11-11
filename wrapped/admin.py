
# Register your models here.
from django.contrib import admin
from .models import SpotifyProfile, SpotifyWrap

admin.site.register(SpotifyProfile)
admin.site.register(SpotifyWrap)
