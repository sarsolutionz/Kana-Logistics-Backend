from django.apps import AppConfig


class MemberAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MemberApp'

    def ready(self):
        import MemberApp.signals  # registers the signal handlers