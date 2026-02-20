import pytest
from django.db import IntegrityError
from dj_shwary.models import ShwaryTransaction
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestShwaryTransaction:
    def test_concurrent_null_shwary_id(self):
        """
        Vérifie que plusieurs transactions peuvent avoir un shwary_id NULL
        en même temps (Test de la correction null=True)
        """

        # Création d'une transaction sans ID shwary
        txn1 = ShwaryTransaction.objects.create(
            amount=5000,
            phone_number="+243840000000",
            shwary_id=None
        )

        # Création d'une deuxième transaction sans ID shwary (Ne dois pas lever d'IntegrityError)
        try:
            txn2 = ShwaryTransaction.objects.create(
                amount=3000,
                phone_number="+243990000001",
                shwary_id=None
            )
        except IntegrityError:
            pytest.fail(
                "Conflit détecté sur shwary_id NULL ! La contrainte unique est mal configurée."
            )

        assert txn1.shwary_id is None
        assert txn2.shwary_id is None
        assert ShwaryTransaction.objects.count() == 2

    def test_unique_constraint_on_real_id(self):
        """
        Vérifie que l'unicité fonctionne toujours pour les vrais  IDs.
        """

        ShwaryTransaction.objects.create(
            amount=10000, phone_number="+243960000024", shwary_id="TRX-123"
        )

        with pytest.raises(IntegrityError):
            # Tentative de créer un doublon de "TRX-123"
            ShwaryTransaction.objects.create(
                amount=1000, phone_number="+243810600026", shwary_id="TRX-123"
            )

    def test_json_serializations_datetime(self):
        """
        Vérifie que le champ raw_response accepte les données de l'API
        (Correction du bug datetime).
        """
        from datetime import datetime

        # Simulation d'un dictionnaire venant du SDK avec un object datetime
        payload_with_date = {
            "id": "shw-7",
            "status": "completed",
            "createdAt": datetime.now(),
        }

        txn = ShwaryTransaction.objects.create(
            amount=20000, phone_number="+243892100026", shwary_id="shw-7"
        )

        # Sans mode="json" ou l'encoder DjangoJSONError, ceci plantera
        try:
            # On teste si le modèle accepte la sauvegarde via l'ORM
            txn.raw_response = payload_with_date
            txn.save()
        except TypeError as e:
            pytest.fail(f"Erreur de sérialisation JSON: {e}")

    def test_generic_relation_link(self):
        """
        Vérifie que la transaction se lie bien à n'importe quel objet
        (ici un User).
        """

        user = User.objects.create_user(
            username="testuser", email="testuser@gmail.com", password="test12@user"
        )

        txn = ShwaryTransaction.objects.create(
            amount=20000, phone_number="+243892100026",
            shwary_id="shw-link", content_object=user   # Liaison générique
        )

        assert txn.content_type.model == "user"
        assert txn.content_object.username == "testuser"
