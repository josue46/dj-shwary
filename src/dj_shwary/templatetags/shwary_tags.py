# shwary_django/templatetags/shwary_tags.py

from django import template
from django.utils.html import format_html
from django.urls import reverse

register = template.Library()

# --- 1. LE FILTRE DE STATUT (Badge) ---

@register.filter(name='shwary_badge')
def status_badge(value):
    """
    Transforme un statut (str ou objet Transaction) en badge HTML.
    Usage: {{ transaction.status|shwary_badge }}
    """
    # Si l'utilisateur passe l'objet Transaction entier au lieu du statut
    if hasattr(value, 'status'):
        value = value.status

    # Mapping des couleurs (Classes CSS standards type Bootstrap/Tailwind)
    # On utilise des styles inline pour que ça marche même sans Bootstrap
    colors = {
        'completed': '#10b981', # Vert Emeraude
        'failed': '#ef4444',    # Rouge
        'cancelled': '#6b7280', # Gris
        'pending': '#f59e0b',   # Orange
        'refunded': '#8b5cf6',  # Violet
    }
    
    color = colors.get(str(value).lower(), '#374151') # Gris foncé par défaut
    label = str(value).capitalize()
    
    style = f"background-color: {color}; color: white; padding: 4px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;"
    
    return format_html('<span style="{}">{}</span>', style, label)


# --- 2. LE BOUTON DE PAIEMENT (Inclusion Tag) ---

@register.inclusion_tag('shwary/pay_button.html')
def shwary_button(target_url, label="Payer avec Shwary", css_class="btn-shwary"):
    """
    Affiche un bouton de paiement (formulaire POST).
    Usage: {% shwary_button url_de_ta_vue "Payer 10$" "btn btn-primary" %}
    """
    return {
        'target_url': target_url,
        'label': label,
        'css_class': css_class,
    }