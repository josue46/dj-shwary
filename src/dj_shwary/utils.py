from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from shwary import Shwary, ShwaryAsync


def get_shwary_client() -> Shwary:
    """
    Retourne une instance configurée du client sync Shwary
    en utilisant les variables définies dans settings.py.
    """

    merchant_id, merchant_key, is_sandbox, timeout = get_shwary_config()

    return Shwary(
        merchant_id=merchant_id,
        merchant_key=merchant_key,
        is_sandbox=is_sandbox,
        timeout=timeout,
    )


# Recupérer le client async
def get_shwary_async_client() -> ShwaryAsync:
    """
    Retourne une instance configurée du client async ShwaryAsync
    en utilisant les variables définies dans settings.py.
    """

    merchant_id, merchant_key, is_sandbox, timeout = get_shwary_config()

    return ShwaryAsync(
        merchant_id=merchant_id,
        merchant_key=merchant_key,
        is_sandbox=is_sandbox,
        timeout=timeout,
    )


def get_shwary_config() -> tuple[str, str, bool, float]:
    """
    Récupère la configuration Shwary depuis settings.py et vérifie sa complétude.
    Retourne les paramètres nécessaires à l'instanciation du client.
    Lève une exception ImproperlyConfigured si la configuration est incomplète.
    """

    shwary = getattr(settings, "SHWARY", {})
    merchant_id: str = shwary.get("MERCHANT_ID")
    merchant_key: str = shwary.get("MERCHANT_KEY")
    is_sandbox: bool = shwary.get("SANDBOX", True)
    timeout: float = shwary.get("TIMEOUT", 30.0)

    if not merchant_id or not merchant_key:
        raise ImproperlyConfigured(
            "La configuration Shwary est incomplète. "
            "Veuillez définir les clés MERCHANT_ID et MERCHANT_KEY dans le dictionnaire SHWARY dans le settings.py"
        )

    return merchant_id, merchant_key, is_sandbox, timeout


def get_webhook_absolute_url(relative_path: str) -> str:
    """
    Tente de construire l'URL absolue du Webhook de la manière la plus fiable possible.
    """
    # Priorité absolue : Une variable définie par le dev
    base_url: str = getattr(settings, "SITE_BASE_URL", None)

    if base_url:
        return f"{base_url.rstrip('/')}{relative_path}"

    # Autrement on utilise le framework Site de Django
    if "django.contrib.sites" in settings.INSTALLED_APPS:
        try:
            domain = Site.objects.get_current().domain
            protocol = "http" if settings.DEBUG else "https"
            return f"{protocol}://{domain}{relative_path}"
        except Exception:
            pass

    raise ImproperlyConfigured(
        "Impossible de générer l'URL absolue du webhook. "
        "Veuillez définir SITE_BASE_URL dans settings.py ou configurez SITE_ID pour resoudre l'erreur."
    )
