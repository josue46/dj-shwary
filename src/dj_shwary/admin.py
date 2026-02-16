import json
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import ShwaryTransaction

@admin.register(ShwaryTransaction)
class ShwaryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'shwary_id', 
        'amount_display', 
        'phone_number', 
        'status_badge', 
        'related_object_link', # Lien vers la commande liée
        'is_sandbox', 
        'created_at'
    )
    
    list_filter = ('status', 'is_sandbox', 'currency', 'created_at')
    
    search_fields = (
        'shwary_id', 
        'phone_number', 
        'object_id', 
        'raw_response' # Recherche même dans le JSON !
    )
    
    date_hierarchy = 'created_at'
    
    # Configuration du formulaire de détail
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'shwary_id', 
        'pretty_raw_response', # JSON formaté
        'related_object_link_detail'
    )

    fieldsets = (
        (_("Identifiants"), {
            'fields': ('shwary_id', 'is_sandbox', 'related_object_link_detail')
        }),
        (_("Finances"), {
            'fields': ('amount', 'currency', 'phone_number')
        }),
        (_("État"), {
            'fields': ('status', 'error_message', 'created_at', 'updated_at')
        }),
        (_("Données Techniques"), {
            'classes': ('collapse',), # Caché par défaut pour ne pas polluer
            'fields': ('content_type', 'object_id', 'pretty_raw_response')
        }),
    )

    def get_queryset(self, request):
        # On pré-charge le content_type pour que related_object_link ne fasse pas une requête par ligne
        return super().get_queryset(request).select_related('content_type')

    # Actions personnalisées
    actions = ['refresh_status_from_api']

    @admin.action(description=_("🔄 Mettre à jour le statut depuis l'API Shwary"))
    def refresh_status_from_api(self, request, queryset):
        """
        Permet à l'admin de forcer la vérification du statut 
        si le webhook n'est pas arrivé.
        """
        success_count = 0
        errors_count = 0

        for txn in queryset:
            if txn.refresh_from_api():
                success_count += 1
            else:
                errors_count += 1
        
        if success_count:
            self.message_user(request, f"{success_count} transactions mises à jour.", messages.SUCCESS)
        if errors_count:
            self.message_user(request, f"{errors_count} erreurs lors de la mise à jour.", messages.ERROR)

    # Méthodes d'affichage (Badges & Liens)

    def amount_display(self, obj):
        return f"{obj.amount:,.2f} {obj.currency}"
    amount_display.short_description = _("Montant")

    def status_badge(self, obj):
        """Affiche un badge coloré selon le statut."""
        colors = {
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'pending': 'orange',
            'refunded': 'purple',
        }
        color = colors.get(obj.status, 'black')
        # Style CSS simple injecté
        style = f"background-color: {color}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold;"
        return format_html('<span style="{}">{}</span>', style, obj.get_status_display())
    status_badge.short_description = _("Statut")

    def related_object_link(self, obj):
        """Crée un lien cliquable vers l'objet lié (ex: la Commande)."""
        if obj.content_object:
            # On construit l'URL admin dynamiquement
            content_type = obj.content_type
            try:
                url = reverse(f'admin:{content_type.app_label}_{content_type.model}_change', args=[obj.object_id])
                return format_html('<a href="{}">{} #{}</a>', url, content_type.model.upper(), obj.object_id)
            except Exception:
                return f"{content_type.model} #{obj.object_id}"
        return "-"
    related_object_link.short_description = _("Concerne")

    def related_object_link_detail(self, obj):
        """Version pour la vue détail (non cliquable dans la liste)."""
        return self.related_object_link(obj)
    related_object_link_detail.short_description = _("Objet lié")

    def pretty_raw_response(self, obj):
        """Affiche le JSON avec une belle indentation."""
        if not obj.raw_response:
            return "-"
        json_str = json.dumps(obj.raw_response, indent=2, sort_keys=True)
        # Affiche dans une balise <pre> pour garder le formatage
        # et ajout de 'white-space: pre-wrap' pour la lisibilité
        style = "background: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-break: break-all;"
        return format_html('<pre style="{}">{}</pre>', style, json_str)
    pretty_raw_response.short_description = _("Réponse API")

    # On empêche la suppression accidentelle de transactions réussies
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'completed' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)