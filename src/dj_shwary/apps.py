from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class DjShwaryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dj_shwary"
    verbose_name = _("Gestion des Paiements Shwary")

    def ready(self):
        # On importe les signaux ici pour s'assurer qu'ils sont enregistrés 
        # dès que l'application est prête.
        try:
            import dj_shwary.signals  # noqa: F401
        except ImportError:
            pass