[![PyPI version](https://img.shields.io/pypi/v/dj-shwary.svg)](https://pypi.org/project/dj-shwary/)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-shwary.svg)](https://pypi.org/project/dj-shwary/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success.svg)](https://pypi.org/project/dj-shwary/)
[![Tests](https://github.com/josue46/dj-shwary/actions/workflows/tests.yml/badge.svg)](https://github.com/josue46/dj-shwary/actions)

# dj-shwary

dj-shwary est le wrapper Django ultime pour intégrer les paiements Shwary (RDC, Kenya, Ouganda) avec élégance et sécurité.

Contrairement à une intégration basique, ce package gère tout le cycle de vie des transactions, du premier clic au "Truth Check" final via webhook.

Résumé des changements v0.1.4
1. Correction Critique (Bug AppRegistryNotReady) :
    Suppression des imports de modèles Django au niveau global dans __init__.py
    pour permettre l'initialisation correcte de Django.
2. Qualité & Tests (CI Ready) :
    Mise en place d'une suite de tests complète avec pytest-django.
    Ajout de 5 tests unitaires couvrant le cycle de vie des transactions (Success, API Failure, Webhook Security, Signals).
    Configuration du fichier pytest.ini et des réglages de test (tests/settings.py).
3. Métadonnées PyPI :
    Ajout des Classifiers officiels (Django 4.2+, Python 3.11+, Production/Stable).
    Correction des liens de badges dans le README.md.
4. Extensibilité :
    Finalisation des Signaux Django (payment_success, payment_failed) pour permettre aux développeurs d'automatiser leurs actions métier.


## Fonctionnalités Clés

Pourquoi utiliser ce wrapper plutôt que de coder l'API à la main ?

| Fonctionnalité | Description |
| :--- | :--- |
| **Liaison Générique** | Liez des transactions à n'importe quel modèle (Order, Subscription, etc.) via `GenericForeignKey`. |
| **Verify by Reference** | Sécurité maximale : le webhook ne fait que "réveiller" le serveur, qui vérifie ensuite le statut réel via l'API Shwary. |
| **Signaux Django** | Découplez votre logique métier (envoi d'email, livraison) grâce aux signaux `payment_success`, `payment_failed`. |
| **Admin Dashboard** | Une interface prête à l'emploi avec badges de couleur, liens vers les objets liés et mise à jour manuelle. |
| **Rattrapage Auto** | Commande `manage.py` pour synchroniser les transactions restées en attente (Cron job). |
| **Template Tags** | Affichez des badges de statut stylisés et des boutons de paiement en une ligne de HTML. |

## Installation

Avec uv (recommandé)

```bash
uv add dj_shwary
```

avec pip

```bash
pip install dj_shwary
```

## Configuration

1. Ajoutez l'application à votre settings.py :

```python
INSTALLED_APPS = [
    ...,
    'django.contrib.contenttypes', # Requis
    'django.contrib.sites',        # Requis pour les URLs absolues
    ...,
    'dj_shwary',
]

SITE_ID = 1
```

2. Ajoutez vos identifiants dans settings.py :

```python
SHWARY = {
    'MERCHANT_ID': 'votre_merchant_id',
    'MERCHANT_KEY': 'votre_merchant_key',
    'SANDBOX': True,  # False en production
    'TIMEOUT': 30.0,  # Timeout en secondes pour les requêtes API
}

# Optionnel : recommandé si vous n'utilisez pas le framework Sites 
# ou pour le développement local avec Ngrok
SITE_BASE_URL = "https://votre-domaine.com"
```

3. Configurez l'URL du Webhook :

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('shwary/', include('dj_shwary.urls')), # Inclut la vue webhook
]
```

## Utilisation

### Initialiser un paiement

Dans votre vue, utilisez le ShwaryService. Il s'occupe de créer la transaction en base et d'appeler l'API.

```python
from dj_shwary.services import ShwaryService

def checkout_view(request, order_id):
    order = Order.objects.get(id=order_id)
    service = ShwaryService()

    transaction = service.make_payment(
        related_object=order,
        amount=order.total_amount,
        phone_number="+243...",
        country="DRC"
    )
    
    return render(request, 'payment_pending.html', {'txn': transaction})
```

### Réagir au succès (Signaux)

Ne polluez pas vos vues. Écoutez simplement le signal quand le paiement est validé.

```python
from django.dispatch import receiver
from dj_shwary.signals import payment_success

@receiver(payment_success)
def handle_order_validation(sender, transaction, **kwargs):
    # 'transaction.content_object' est votre instance de Order !
    order = transaction.content_object
    order.mark_as_paid()
    order.save()
```

### Frontend (Template Tags)

Affichez un badge de statut élégant dans vos templates :

```html
{% load shwary_tags %}

<p>Statut de la commande : {{ transaction|shwary_badge }}</p>
```

## Maintenance & Fiabilité

### Interface Admin

Le dashboard admin permet de voir en un coup d'œil les transactions échouées et de forcer une mise à jour via l'action "Mettre à jour le statut depuis l'API Shwary".

### Commande de rattrapage

Si un webhook est perdu à cause d'une coupure réseau, lancez cette commande via un Cron job toutes les 10 minutes :

```bash
python manage.py check_pending_pay --older-than 5
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une Issue ou une Pull Request sur le dépôt GitHub.

Distribué sous la licence MIT. Voir [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) pour plus d'informations.

## FAQ & Troubleshooting
1. Pourquoi mon Webhook renvoie-t-il une erreur 404 ?

Vérifiez deux points :

    Avez-vous bien inclus path('shwary/', include('dj_shwary.urls')) dans votre fichier urls.py principal ?

    Si vous testez en local, l'API Shwary ne peut pas voir votre localhost. Vous devez utiliser un tunnel comme Ngrok ou Cloudflare Tunnel et configurer SITE_BASE_URL avec l'URL fournie par le tunnel.

2. Le Webhook renvoie une erreur 403 (CSRF Forbidden)

C'est normal si vous essayez de le tester manuellement. Cependant, la vue ShwaryWebhookView est déjà protégée par le décorateur @csrf_exempt. Si l'erreur persiste, vérifiez que votre proxy inverse (Nginx/Apache) ne bloque pas les requêtes POST entrantes.

3. Comment accéder à ma commande depuis une transaction ?

Grâce au système de GenericForeignKey, c'est très simple :
```python
# Dans un signal ou une vue :
mon_objet = transaction.content_object 

# S'il s'agit d'une commande :
print(mon_objet.order_number)
```

4. Erreur "Site matching query does not exist"

Si vous n'utilisez pas SITE_BASE_URL, le wrapper tente d'utiliser le framework sites de Django. Assurez-vous d'avoir défini SITE_ID = 1 dans vos settings.py et que le domaine est correctement configuré dans l'interface d'administration Django.

5. Puis-je utiliser Shwary en mode test ?

Oui. Assurez-vous que dans le dictionnaire SHWARY dans le settings, la clé SANDBOX soit True dans vos réglages. Le wrapper utilisera alors les endpoints de test de Shwary et marquera les transactions comme étant en mode sandbox dans l'admin.
