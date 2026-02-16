from typing import Literal
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from shwary import Shwary, ShwaryError

from .utils import get_shwary_config, get_webhook_absolute_url
from .models import ShwaryTransaction


class ShwaryService:
    """
    Service de paiement Shwary pour Django.
    - Encapsule la logique métier de création de paiement et de gestion des transactions.
    - Interagit avec le SDK Shwary pour initier les paiements et vérifier les statuts.
    - Gère la création et la mise à jour des objets ShwaryTransaction en base.
    - Peut être utilisé par les vues ou d'autres services métier pour intégrer Shwary de manière transparente.
    - Permet de centraliser la configuration et les appels API liés à Shwary, facilitant ainsi la maintenance et les évolutions futures.
    - Gère les erreurs de manière robuste pour éviter les incohérences dans la base de données et fournir des feedbacks clairs à l'utilisateur ou au développeur.
    """

    def __init__(self):
        self.merchant_id, self.merchant_key, self.is_sandbox, self.timeout = (
            get_shwary_config()
        )

        self.client = Shwary(
            merchant_id=self.merchant_id,
            merchant_key=self.merchant_key,
            is_sandbox=self.is_sandbox,
            timeout=self.timeout,
        )

    def make_payment(
        self,
        related_object,
        amount,
        phone_number: str,
        country: Literal["DRC", "KE", "UG"] = "DRC",
        currency: str = "CDF",
        callback_url: str | None = None,
    ) -> ShwaryTransaction:
        """
        Crée une transaction locale et initie le paiement sur l'API Shwary.

        Args:
            related_object: L'objet Django lié à cette transaction (ex: une commande, un abonnement, etc.)
            amount: Montant (Decimal ou float)
            phone_number: Numéro du client
            country: Code pays (DRC, KE, UG)

        Returns:
            ShwaryTransaction: L'instance créée ou mise à jour avec les infos de Shwary.
        """

        # Préparation de la liaison générique (GenericForeignKey)
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = str(related_object.pk)

        # Création de la transaction locale (État INITIAL)
        # On crée l'objet AVANT l'appel API pour avoir une trace même si ça crash.
        txn: ShwaryTransaction = ShwaryTransaction.objects.create(
            content_type=content_type,
            object_id=object_id,
            amount=amount,
            currency=currency,
            phone_number=phone_number,
            is_sandbox=self.is_sandbox,
            status=ShwaryTransaction.Status.PENDING,
            error_message="Initiating...",
        )

        if not callback_url:
            # Si callback_url n'est pas fourni, on génère une par défaut
            relative_url = reverse("dj_shwary:webhook")
            callback_url = get_webhook_absolute_url(relative_url)

        try:
            # Appel API via le SDK
            response = self.client.initiate_payment(
                country=country,
                amount=amount,
                phone_number=phone_number,
                callback_url=callback_url,
            )

            # Mise à jour succès (On a l'ID Shwary !)
            txn.shwary_id = response.id
            txn.status = response.status
            txn.raw_response = response.model_dump()
            txn.error_message = None  # Clean up
            txn.save(
                update_fields=(
                    "shwary_id",
                    "status",
                    "raw_response",
                    "error_message",
                    "updated_at",
                )
            )

            return txn

        except Exception as e:
            txn.status = ShwaryTransaction.Status.FAILED
            txn.error_message = str(e)

            # Si c'est une erreur API structurée, on peut extraire plus de détails
            if hasattr(e, "raw_response"):
                txn.raw_response = e.raw_response

            txn.save(update_fields=("status", "error_message", "updated_at"))

            # On relève l'exception pour que le contrôleur (View) puisse afficher un message à l'utilisateur
            raise ShwaryError from e

    def check_status(self, transaction_id):
        """
        Force la vérification du statut d'une transaction (Polling).
        Utile si le webhook n'est jamais arrivé.
        """
        try:
            # Récupération locale
            txn = ShwaryTransaction.objects.get(shwary_id=transaction_id)

            # Appel API
            api_response = self.client.get_transaction(transaction_id)

            # Mise à jour si changement
            if txn.status != api_response.status:
                txn.status = api_response.status
                txn.raw_response = api_response.model_dump()
                txn.save(update_fields=("status", "raw_response", "updated_at"))

            return api_response.status

        except ShwaryTransaction.DoesNotExist:
            return None
