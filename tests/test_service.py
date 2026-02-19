import pytest
from unittest.mock import MagicMock
from dj_shwary.services import ShwaryService
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_make_payment_creates_transaction():
    # 1. Setup : On crée un objet lié (ex: un User)
    user = User.objects.create(username="testuser")
    
    # 2. Mock du client Shwary pour ne pas appeler l'API
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.id = "SHW-123"
    mock_response.status = "PENDING"
    mock_response.model_dump.return_value = {"id": "SHW-123", "status": "PENDING"}
    mock_client.initiate_payment.return_value = mock_response

    # 3. Action
    service = ShwaryService(client=mock_client)
    txn = service.make_payment(
        related_object=user,
        amount=1000,
        phone_number="243810000000"
    )

    # 4. Assert
    assert txn.shwary_id == "SHW-123"
    assert txn.amount == 1000
    assert txn.status == "PENDING"


@pytest.mark.django_db
def test_make_payment_api_failure():
    user = User.objects.create(username="failuser")
    
    # On simule une erreur du SDK Shwary
    mock_client = MagicMock()
    mock_client.initiate_payment.side_effect = Exception("API Connection Timeout")

    service = ShwaryService(client=mock_client)
    
    # On vérifie que le service relance bien l'exception ShwaryError
    from shwary import ShwaryError
    with pytest.raises(ShwaryError):
        service.make_payment(
            related_object=user,
            amount=500,
            phone_number="243810000001"
        )

    # On vérifie que la transaction a bien été enregistrée comme échouée en base
    from dj_shwary.models import ShwaryTransaction
    txn = ShwaryTransaction.objects.get(phone_number="243810000001")
    assert txn.status == ShwaryTransaction.Status.FAILED
    assert "API Connection Timeout" in txn.error_message
