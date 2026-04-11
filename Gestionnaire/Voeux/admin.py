from django.contrib import admin
from .models import (TypeContribution, Voeu, VersementVoeu, Contribution,
                     VersementContribution, HistoriqueVoeu, HistoriqueContribution,
                     HistoriqueVersementVoeu, HistoriqueVersementContribution)

# Niveaux autorisés à supprimer un historique
_PEUT_SUPPRIMER_HISTORIQUE = {'ADMIN', 'REGION', 'GROUPE'}


def _peut_supprimer_historique(user):
    """True si l'utilisateur a le droit de supprimer des entrées d'historique."""
    if user.is_superuser:
        return True
    if hasattr(user, 'profile') and user.profile.niveau_acces in _PEUT_SUPPRIMER_HISTORIQUE:
        return True
    return False


# ─── TypeContribution ─────────────────────────────────────────────────────────

@admin.register(TypeContribution)
class TypeContributionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif', 'ordre', 'created')
    list_editable = ('actif', 'ordre')


# ─── VOEU ─────────────────────────────────────────────────────────────────────

class VersementVoeuInline(admin.TabularInline):
    model = VersementVoeu
    extra = 0
    readonly_fields = ('auteur', 'created')


class HistoriqueVersementVoeuInline(admin.TabularInline):
    model = HistoriqueVersementVoeu
    extra = 0
    readonly_fields = ('ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    max_num = 0

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_add_permission(self, request, obj=None):
        return False


class HistoriqueVoeuInline(admin.TabularInline):
    model = HistoriqueVoeu
    extra = 0
    readonly_fields = ('ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    # Pas de nouveau enregistrement possible
    max_num = 0

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Voeu)
class VoeuAdmin(admin.ModelAdmin):
    list_display = ('membre', 'eglise', 'date_voeu', 'montant_promis',
                    'total_paye', 'montant_restant', 'est_solde')
    list_filter = ('eglise__region', 'eglise__groupe', 'date_voeu')
    search_fields = ('membre__nom', 'membre__prenom', 'eglise__nom')
    inlines = [VersementVoeuInline, HistoriqueVoeuInline]
    date_hierarchy = 'date_voeu'


@admin.register(HistoriqueVersementVoeu)
class HistoriqueVersementVoeuAdmin(admin.ModelAdmin):
    list_display = ('versement', 'ancien_montant', 'nouveau_montant', 'auteur', 'created')
    list_filter = ('versement__voeu__eglise__region', 'created')
    search_fields = ('versement__voeu__membre__nom', 'versement__voeu__membre__prenom', 'justification')
    readonly_fields = ('versement', 'ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_change_permission(self, request, obj=None):
        return False


# ─── CONTRIBUTION ─────────────────────────────────────────────────────────────

class VersementContribInline(admin.TabularInline):
    model = VersementContribution
    extra = 0
    readonly_fields = ('auteur', 'created')


class HistoriqueVersementContribInline(admin.TabularInline):
    model = HistoriqueVersementContribution
    extra = 0
    readonly_fields = ('ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    max_num = 0

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_add_permission(self, request, obj=None):
        return False


class HistoriqueContribInline(admin.TabularInline):
    model = HistoriqueContribution
    extra = 0
    readonly_fields = ('ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    max_num = 0

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('membre', 'eglise', 'type_contribution', 'date_contribution',
                    'total_verse', 'montant_objectif')
    list_filter = ('type_contribution', 'eglise__region', 'eglise__groupe', 'date_contribution')
    search_fields = ('membre__nom', 'membre__prenom', 'eglise__nom')
    inlines = [VersementContribInline, HistoriqueContribInline]
    date_hierarchy = 'date_contribution'


@admin.register(HistoriqueVersementContribution)
class HistoriqueVersementContributionAdmin(admin.ModelAdmin):
    list_display = ('versement', 'ancien_montant', 'nouveau_montant', 'auteur', 'created')
    list_filter = ('versement__contribution__eglise__region', 'created')
    search_fields = ('versement__contribution__membre__nom', 'versement__contribution__membre__prenom', 'justification')
    readonly_fields = ('versement', 'ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_change_permission(self, request, obj=None):
        return False


# ─── Accès direct aux historiques (vue liste admin) ───────────────────────────

@admin.register(HistoriqueVoeu)
class HistoriqueVoeuAdmin(admin.ModelAdmin):
    list_display = ('voeu', 'ancien_montant', 'nouveau_montant', 'auteur', 'created')
    list_filter = ('voeu__eglise__region', 'voeu__eglise__groupe', 'created')
    search_fields = ('voeu__membre__nom', 'voeu__membre__prenom', 'voeu__eglise__nom', 'justification')
    readonly_fields = ('voeu', 'ancien_montant', 'nouveau_montant', 'justification', 'auteur', 'created')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HistoriqueContribution)
class HistoriqueContributionAdmin(admin.ModelAdmin):
    list_display = ('contribution', 'ancien_montant', 'nouveau_montant', 'auteur', 'created')
    list_filter = ('contribution__eglise__region', 'contribution__eglise__groupe', 'created')
    search_fields = ('contribution__membre__nom', 'contribution__membre__prenom',
                     'contribution__eglise__nom', 'justification')
    readonly_fields = ('contribution', 'ancien_montant', 'nouveau_montant',
                       'justification', 'auteur', 'created')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return _peut_supprimer_historique(request.user)

    def has_change_permission(self, request, obj=None):
        return False
