from django.apps import AppConfig


class WrappedAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wrapped_app'
