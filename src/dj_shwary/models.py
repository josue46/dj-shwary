import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ShwaryTransaction(models.Model):
    """
    Modèle pour stocker les transactions de paiement Shwary.
    Utilise des GenericForeignKeys pour se lier à n'importe quel modèle.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        COMPLETED = "completed", _("Réussi")
        FAILED = "failed", _("Échoué")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shwary_id = models.CharField(
        _("ID Shwary"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("L'identifiant unique retourné par l'API Shwary"),
    )
    amount = models.DecimalField(_("Montant"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Devise"), max_length=3, default="CDF")
    phone_number = models.CharField(
        _("Numéro de téléphone"),
        max_length=20,
        help_text=_("Format E.164 (ex. +243...)"),
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    is_sandbox = models.BooleanField(
        _("Mode Sandbox"),
        default=True,
        help_text=_("Vrai si la transaction a été faite en environnement de teste."),
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.CharField(max_length=50, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    raw_response = models.JSONField(
        _("Réponse API brute"),
        default=dict,
        blank=True,
        help_text=_("Stocke la réponse complète de Shwary pour débogage."),
    )
    error_message = models.TextField(_("Message d'erreur"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Transaction Shwary")
        verbose_name_plural = _("Transactions Shwary")
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=("shwary_id", "status")),
            models.Index(fields=("content_type", "object_id")),
        )
    
    def __str__(self) -> str:
        return f"{self.shwary_id} - {self.amount} {self.currency} ({self.get_status_display()})"
    
    @property
    def is_successful(self) -> bool:
        return self.status == self.Status.COMPLETED
    
    def refresh_from_api(self, client=None) -> bool:
        """
        Met à jour le statut de la transaction en interrogeant l'API Shwary.

        Args:
            client: Instance de shwary.Shwary (optionenel)
        """

        from dj_shwary.utils import get_shwary_client
        

        if not client:
            client = get_shwary_client()
        
        try:
            response = client.get_transaction(self.shwary_id)

            if response.status != self.status:
                self.status = response.status
                self.raw_response = response.model_dump()
                self.save(update_fields=("status", "raw_response", "updated_at"))
             
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur update transaction {self.shwary_id}: {e}")
            return False
