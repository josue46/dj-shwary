import json
import logging

from django.views import View
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction

from dj_shwary.services import ShwaryService

from .models import ShwaryTransaction
from .signals import payment_success, payment_status_changed, payment_failed

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ShwaryWebhookView(View):
    """
    Vue générique pour recevoir les notifications de Shwary.
    1. Utilise le pattern 'Verify by Reference' pour pallier l'absence de signature.
    2. Met à jour la transaction en base
    3. Envoie Signal Django pour que l'app métier réagisse.
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        shwary_id = payload.get("id")
        webhook_status = payload.get("status")

        if not shwary_id or not webhook_status:
            return HttpResponseBadRequest("Missing ID or Status")

        logger.info(f"Webhook reçu pour {shwary_id} prétendant être: {webhook_status}")

        # --- COUCHE DE SÉCURITÉ : VERIFY BY REFERENCE ---
        try:
            # On utilise le service pour lire la vérité depuis l'API.
            service = ShwaryService()
            api_response = service.client.get_transaction(shwary_id)
            real_status = api_response.status

        except Exception as e:
            logger.error(f"Impossible de vérifier le statut auprès de l'API Shwary pour {shwary_id}: {e}")
            # Très important : Si l'API Shwary est down, on refuse le webhook (500).
            return HttpResponse("Verification failed, try again later", status=500)

        if real_status != webhook_status:
            logger.warning(
                f"ALERTE SÉCURITÉ : Discordance détectée pour {shwary_id} ! "
                f"Webhook: '{webhook_status}' vs API: '{real_status}'. "
                f"La valeur de l'API est retenue."
            )

        # Le statut et le payload de confiance sont ceux de l'API
        trusted_status = real_status
        payload = api_response.model_dump()

        # --- MISE À JOUR ATOMIQUE EN BASE ---
        try:
            with db_transaction.atomic():
                txn = (
                    ShwaryTransaction.objects.select_for_update()
                    .filter(shwary_id=shwary_id)
                    .first()
                )

                if not txn:
                    logger.warning(f"Transaction {shwary_id} introuvable localement.")
                    return HttpResponse("Transaction not found, ignored", status=200)

                previous_status = txn.status

                # On met à jour avec le statut DE CONFIANCE
                txn.status = trusted_status
                txn.raw_response = payload
                txn.save(update_fields=("status", "raw_response", "updated_at"))

                # --- DISPATCH DES SIGNAUX ---
                _signal_params = {
                    "sender": self.__class__,
                    "transaction": txn,
                    "raw_data": payload,
                }

                if previous_status != trusted_status:
                    payment_status_changed.send(**_signal_params)

                    match trusted_status:
                        case ShwaryTransaction.Status.COMPLETED:
                            payment_success.send(**_signal_params)
                        case ShwaryTransaction.Status.FAILED:
                            payment_failed.send(**_signal_params)

            return HttpResponse("OK", status=200)

        except Exception as e:
            logger.exception(f"Erreur critique lors de l'enregistrement du webhook: {e}")
            return HttpResponse("Internal Error", status=500)
