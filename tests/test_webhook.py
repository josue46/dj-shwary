import pytest
import json
from django.urls import reverse
from dj_shwary.models import ShwaryTransaction

@pytest.mark.django_db
def test_webhook_updates_status_and_triggers_signal(client, mocker):
    # 1. Préparer une transaction locale
    txn = ShwaryTransaction.objects.create(
        shwary_id="test-123",
        amount=100,
        status="pending"
    )

    # 2. Mocker le signal pour vérifier s'il est appelé
    signal_handler = mocker.patch('dj_shwary.signals.payment_success.send')

    # 3. Simuler un appel Webhook de Shwary
    payload = {
        "id": "test-123",
        "status": "completed",
        "amount": 100
    }
    
    url = reverse('shwary-webhook')
    response = client.post(
        url, 
        data=json.dumps(payload), 
        content_type='application/json'
    )

    # 4. Vérifications
    assert response.status_code == 200
    txn.refresh_from_db()
    assert txn.status == "completed"
    assert signal_handler.called