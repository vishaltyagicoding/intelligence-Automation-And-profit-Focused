from django.apps import AppConfig


class ReversalZonesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reversal_zones'
    
    def ready(self):
        """Import signal handlers when Django starts."""
        import reversal_zones.signals  # noqa: F401
