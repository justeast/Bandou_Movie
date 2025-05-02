from django.apps import AppConfig


class BandouConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bandou"

    def ready(self):
        import bandou.utils.signals  # noqa: F401
