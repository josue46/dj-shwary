from django.dispatch import Signal

# Signal envoyé quand un paiement réussit
# Arguments: sender, transaction (instance du modèle), raw_data (dict)
payment_success = Signal()

# Signal envoyé quand un paiement échoue
payment_failed = Signal()

# Signal générique pour tout changement de statut
payment_status_changed = Signal()
