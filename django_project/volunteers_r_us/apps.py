from django.apps import AppConfig

class VolunteersRUsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "volunteers_r_us"

    def ready(self):
        # import signal handlers
        from . import signals  # noqa: F401
