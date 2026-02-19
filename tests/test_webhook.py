import json
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from dj_shwary.models import ShwaryTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_webhook_success_updates_transaction(client):
    # 1. Setup : On crée une transaction en attente dans notre base
    user = User.objects.create(username="webhookuser")
    txn = ShwaryTransaction.objects.create(
        shwary_id="SHW-999",
        content_object=user,
        amount=5000,
        status=ShwaryTransaction.Status.PENDING
    )

    # 2. Mock de l'API Shwary (Sécurité : Verify by Reference)
    # On patche ShwaryService pour qu'il renvoie un statut COMPLETED
    with patch("dj_shwary.views.ShwaryService") as MockService:
        mock_instance = MockService.return_value
        mock_api_res = MagicMock()
        mock_api_res.status = "completed"
        mock_api_res.model_dump.return_value = {"id": "SHW-999", "status": "completed"}
        mock_instance.client.get_transaction.return_value = mock_api_res

        # 3. Action : On simule l'envoi du Webhook par Shwary
        url = reverse("dj_shwary:webhook")
        payload = {"id": "SHW-999", "status": "completed"}
        
        response = client.post(
            url, 
            data=json.dumps(payload), 
            content_type="application/json"
        )

        # 4. Assertions
        assert response.status_code == 200
        txn.refresh_from_db()
        assert txn.status == ShwaryTransaction.Status.COMPLETED
        assert txn.raw_response["status"] == "completed"

@pytest.mark.django_db
def test_webhook_security_mismatch(client):
    """Vérifie que si le webhook ment, on croit l'API (Verify by Reference)"""
    user = User.objects.create(username="hacker")
    txn = ShwaryTransaction.objects.create(
        shwary_id="SHW-FAKE",
        content_object=user,
        amount=100,
        status=ShwaryTransaction.Status.PENDING
    )

    with patch("dj_shwary.views.ShwaryService") as MockService:
        mock_instance = MockService.return_value
        mock_api_res = MagicMock()
        # L'API dit FAILED alors que le webhook dira completed
        mock_api_res.status = "failed"
        mock_api_res.model_dump.return_value = {"status": "failed"}
        mock_instance.client.get_transaction.return_value = mock_api_res

        # Le "hacker" envoie un webhook prétendant que c'est payé
        payload = {"id": "SHW-FAKE", "status": "completed"}
        client.post(reverse("dj_shwary:webhook"), data=json.dumps(payload), content_type="application/json")

        txn.refresh_from_db()
        # On vérifie que la transaction est FAILED car on a cru l'API
        assert txn.status == ShwaryTransaction.Status.FAILED
