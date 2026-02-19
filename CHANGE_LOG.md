Résumé des changements (Changelog 0.1.2)
1. Correction Critique (Bug AppRegistryNotReady) :
    Suppression des imports de modèles Django au niveau global dans __init__.py et services.py.
    Utilisation d'imports locaux (différés) pour permettre l'initialisation correcte de Django.
2. Sécurité Renforcée (Webhook) :
    Implémentation du pattern "Verify by Reference" : Chaque notification reçue par le Webhook est désormais re-vérifiée directement auprès de l'API Shwary pour éviter les injections de faux paiements.
3. Qualité & Tests (CI Ready) :
    Mise en place d'une suite de tests complète avec pytest-django.
    Ajout de 5 tests unitaires couvrant le cycle de vie des transactions (Success, API Failure, Webhook Security, Signals).
    Configuration du fichier pytest.ini et des réglages de test (tests/settings.py).
4. Métadonnées PyPI :
    Ajout des Classifiers officiels (Django 4.2+, Python 3.11+, Production/Stable).
    Correction des liens de badges dans le README.md.
5. Extensibilité :
    Finalisation des Signaux Django (payment_success, payment_failed) pour permettre aux développeurs d'automatiser leurs actions métier.
