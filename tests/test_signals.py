import json
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from dj_shwary.models import ShwaryTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_webhook_triggers_payment_success_signal(client):
    """
    Vérifie que le signal payment_success est bien envoyé avec la transaction
    lorsqu'un webhook valide (confirmé par l'API) arrive.
    """
    # 1. Préparation des données
    user = User.objects.create(username="signal_user")
    txn = ShwaryTransaction.objects.create(  # noqa: F841
        shwary_id="SHW-SIG-123",
        content_object=user,
        amount=1500,
        status=ShwaryTransaction.Status.PENDING
    )

    # 2. On patche à la fois le Service (pour l'API) et le Signal (pour l'espionner)
    with patch("dj_shwary.views.ShwaryService") as MockService, \
         patch("dj_shwary.signals.payment_success.send") as mock_payment_signal:
        
        # Configuration du mock API (on renvoie 'completed')
        mock_instance = MockService.return_value
        mock_api_res = MagicMock()
        mock_api_res.status = "completed"
        mock_api_res.model_dump.return_value = {"id": "SHW-SIG-123", "status": "completed"}
        mock_instance.client.get_transaction.return_value = mock_api_res

        # 3. Simulation du Webhook
        url = reverse("dj_shwary:webhook")
        payload = {"id": "SHW-SIG-123", "status": "completed"}
        
        client.post(
            url, 
            data=json.dumps(payload), 
            content_type="application/json"
        )

        # 4. Assertions sur le signal
        # On vérifie que le signal a été appelé exactement une fois
        assert mock_payment_signal.called
        assert mock_payment_signal.call_count == 1
        
        # On vérifie les arguments envoyés au signal
        # sender doit être la classe ShwaryWebhookView, transaction doit être notre objet txn
        call_kwargs = mock_payment_signal.call_args.kwargs
        assert call_kwargs["transaction"].shwary_id == "SHW-SIG-123"
        assert call_kwargs["transaction"].status == "completed"
        assert "raw_data" in call_kwargs
