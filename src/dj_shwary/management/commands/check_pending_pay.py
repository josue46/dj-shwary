# shwary_django/management/commands/check_pending_shwary.py
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from dj_shwary.models import ShwaryTransaction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Vérifie et met à jour les transactions Shwary en attente (polling de rattrapage).'

    def add_arguments(self, parser):
        # Permet de filtrer : ne pas vérifier les transactions créées il y a 10 secondes
        parser.add_argument(
            '--older-than',
            type=int,
            default=5,
            help='Ignorer les transactions créées il y a moins de X minutes (défaut: 5)'
        )

    def handle(self, *args, **options):
        minutes = options['older_than']
        cutoff_time = timezone.now() - timedelta(minutes=minutes)

        # On cherche les transactions PENDING qui sont assez vieilles
        pending_txns = ShwaryTransaction.objects.filter(
            status=ShwaryTransaction.Status.PENDING,
            created_at__lte=cutoff_time
        )

        count = pending_txns.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucune transaction en attente à vérifier."))
            return

        self.stdout.write(f"Vérification de {count} transactions en attente...")

        updated_count = 0
        errors_count = 0

        for txn in pending_txns:
            try:
                self.stdout.write(f"  - Vérification {txn.shwary_id}...", ending='')
                
                # C'est ici que la magie opère : on utilise la méthode du modèle
                # qui va utiliser get_shwary_client en interne
                if txn.refresh_from_api():
                    # Si le statut a changé (plus PENDING)
                    if txn.status != ShwaryTransaction.Status.PENDING:
                        self.stdout.write(self.style.SUCCESS(f" OK -> {txn.status}"))
                        updated_count += 1
                    else:
                        self.stdout.write(" Toujours Pending")
                else:
                    self.stdout.write(self.style.ERROR(" Erreur API"))
                    errors_count += 1
                    
            except Exception as e:
                logger.error(f"Erreur commande check_pending pour {txn.shwary_id}: {e}")
                self.stdout.write(self.style.ERROR(f" Exception: {e}"))
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminé. {updated_count} mises à jour, {errors_count} erreurs sur {count} transactions."
        ))