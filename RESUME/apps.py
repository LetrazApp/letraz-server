from django.apps import AppConfig


class ResumeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'RESUME'
    
    def ready(self):
        """Import signals when the app is ready"""
        import RESUME.signals