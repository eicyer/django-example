from django.apps import AppConfig


class TournAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tourn_admin'
    
class TournInfoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tourn_info'

    def ready(self):
        import tourn_info.signals
