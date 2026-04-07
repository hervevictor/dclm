from django import template

register = template.Library()

# Régions qui utilisent la nomenclature Grand Lomé
# (Groupe = intermédiaire, District = église locale)
REGIONS_GRAND_LOME = ['lomé', 'lome', 'grand lomé', 'grand lome']


def is_grand_lome(region_name):
    """Retourne True si la région utilise la nomenclature Grand Lomé."""
    if not region_name:
        return True  # Par défaut on garde la nomenclature actuelle
    return any(k in region_name.lower() for k in REGIONS_GRAND_LOME)


def get_labels(region_name):
    """
    Retourne un dict avec les bons labels selon la région.
    Grand Lomé  : intermediaire='Groupe',   local='District'
    Autres      : intermediaire='District', local='Groupe'
    """
    if is_grand_lome(region_name):
        return {
            'intermediaire': 'Groupe',
            'intermediaire_pl': 'Groupes',
            'local': 'District',
            'local_pl': 'Districts',
        }
    return {
        'intermediaire': 'District',
        'intermediaire_pl': 'Districts',
        'local': 'Localité',
        'local_pl': 'Localités',
    }


# ── Template tags ─────────────────────────────────────────────────────────────

@register.filter
def label_intermediaire(region_name):
    """{{ eglise.region|label_intermediaire }} → 'Groupe' ou 'District'"""
    return get_labels(region_name)['intermediaire']


@register.filter
def label_intermediaire_pl(region_name):
    return get_labels(region_name)['intermediaire_pl']


@register.filter
def label_local(region_name):
    """{{ eglise.region|label_local }} → 'District' ou 'Groupe'"""
    return get_labels(region_name)['local']


@register.filter
def label_local_pl(region_name):
    return get_labels(region_name)['local_pl']


@register.simple_tag
def labels_for(region_name):
    """{% labels_for eglise.region as lbl %} → dict complet"""
    return get_labels(region_name)
