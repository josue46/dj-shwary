# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2026-02-20

### Ajouté
- **Modèle de Transaction** : Système robuste utilisant `GenericForeignKey` pour lier les paiements à n'importe quel modèle Django (Commandes, Dons, etc.).
- **Webhook Sécurisé** : Implémentation du pattern "Verify by Reference" qui interroge l'API Shwary pour confirmer le statut réel de la transaction.
- **Service Shwary** : Classe `ShwaryService` pour faciliter l'initialisation des paiements et le suivi.
- **Signaux Django** : Ajout de `payment_success`, `payment_failed` et `payment_status_changed` pour un découplage total de la logique métier.
- **Interface Admin** : Dashboard enrichi avec badges de couleur, liens dynamiques vers les objets liés et action manuelle de mise à jour via API.
- **Suite de Tests** : Tests unitaires avec `pytest` couvrant la concurrence de base de données, la sérialisation JSON et l'unicité des IDs.
- **Template Tags** : Inclusion de `shwary_tags` pour afficher des badges de statut stylisés dans le frontend.

### Corrigé
- **Concurrence SQL** : Passage de `shwary_id` en `null=True` pour permettre plusieurs transactions simultanées en attente (correction du conflit `UNIQUE` sur les valeurs vides).
- **Sérialisation JSON** : Résolution de l'erreur `TypeError: Object of type datetime is not JSON serializable` en utilisant le mode JSON de Pydantic lors de l'enregistrement de la réponse brute.
- **Race Condition** : La vue Webhook renvoie désormais une erreur `404` au lieu d'un `200` si la transaction n'est pas encore enregistrée localement, permettant une relance (retry) automatique par le fournisseur.

### Sécurité
- Protection CSRF désactivée spécifiquement pour l'endpoint du Webhook via `@csrf_exempt`.
- Validation stricte des statuts : le statut de l'API Shwary prévaut toujours sur le payload envoyé par le Webhook.

---

[0.1.6]: https://github.com/josue46/dj-shwary/releases/tag/v0.1.6