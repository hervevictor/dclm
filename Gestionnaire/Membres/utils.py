from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


# ─── Mixins CBV ────────────────────────────────────────────────────────────────

class RBACMixin(LoginRequiredMixin):
    """Mixin de base : exige d'être connecté. Redirige vers la page de connexion."""
    login_url = '/membres/login/'


class AdminOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réservé aux ADMIN et superusers."""
    login_url = '/membres/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return hasattr(user, 'profile') and user.profile.niveau_acces == 'ADMIN'


class AdminComptableMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réservé aux ADMIN, COMPTABLE et superusers."""
    login_url = '/membres/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return hasattr(user, 'profile') and user.profile.niveau_acces in ['ADMIN', 'COMPTABLE']


# ─── Décorateurs FBV ───────────────────────────────────────────────────────────

def admin_required(view_func):
    """Décorateur FBV : réservé aux ADMIN et superusers."""
    @wraps(view_func)
    @login_required(login_url='/membres/login/')
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(user, 'profile') and user.profile.niveau_acces == 'ADMIN':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def admin_comptable_required(view_func):
    """Décorateur FBV : réservé aux ADMIN, COMPTABLE et superusers."""
    @wraps(view_func)
    @login_required(login_url='/membres/login/')
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(user, 'profile') and user.profile.niveau_acces in ['ADMIN', 'COMPTABLE']:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


# ─── Filtre RBAC QuerySet ──────────────────────────────────────────────────────

def filter_by_rbac(user, queryset, model_type='eglise'):
    """
    Filtre un QuerySet Django en fonction du niveau d'accès de l'utilisateur.

    Arguments:
        user: l'instance request.user
        queryset: le QuerySet (ex: Eglise.objects.all(), Adulte.objects.all())
        model_type: 'eglise', 'groupe', 'region', 'adulte', 'jeune', 'enfant',
                    'membre', 'transaction', 'bilan'
    """
    # Superuser ou ADMIN/COMPTABLE → tout voir
    if user.is_superuser:
        return queryset

    if getattr(user, 'is_staff', False) and not hasattr(user, 'profile'):
        return queryset  # Anciens admins sans profil

    if not hasattr(user, 'profile'):
        return queryset.none()  # Aucun profil → aucune donnée

    profil = user.profile
    if profil.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return queryset

    # ── Eglise ──────────────────────────────────────────────────────────────
    if model_type == 'eglise':
        if profil.niveau_acces == 'REGION' and profil.region_assignee:
            return queryset.filter(region__icontains=profil.region_assignee)
        elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
            return queryset.filter(groupe__icontains=profil.groupe_assigne)
        elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
            return queryset.filter(nom__icontains=profil.district_assigne)

    # ── Groupe ──────────────────────────────────────────────────────────────
    elif model_type == 'groupe':
        if profil.niveau_acces == 'REGION' and profil.region_assignee:
            return queryset.filter(region__icontains=profil.region_assignee)
        elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
            return queryset.filter(name__icontains=profil.groupe_assigne)
        elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
            from Eglises.models import Eglise
            eglises_du_district = Eglise.objects.filter(nom__icontains=profil.district_assigne)
            if eglises_du_district.exists():
                noms_groupes = eglises_du_district.values_list('groupe', flat=True)
                return queryset.filter(name__in=noms_groupes)
            return queryset.none()

    # ── Région ──────────────────────────────────────────────────────────────
    elif model_type == 'region':
        if profil.niveau_acces == 'REGION' and profil.region_assignee:
            return queryset.filter(name__icontains=profil.region_assignee)
        elif profil.niveau_acces in ['GROUPE', 'DISTRICT']:
            from Eglises.models import Eglise
            if profil.niveau_acces == 'DISTRICT':
                eglises = Eglise.objects.filter(nom__icontains=profil.district_assigne)
            else:
                eglises = Eglise.objects.filter(groupe__icontains=profil.groupe_assigne)
            if eglises.exists():
                regions_concernees = eglises.values_list('region', flat=True)
                return queryset.filter(name__in=regions_concernees)
            return queryset.none()

    # ── Membres (Adultes, Jeunes, Enfants) ──────────────────────────────────
    elif model_type in ['adulte', 'jeune', 'enfant', 'membre']:
        # Vérification de la section assignée
        if profil.section_assignee != 'TOUS':
            section_map = {'adulte': 'ADULTES', 'jeune': 'JEUNES', 'enfant': 'ENFANTS'}
            if profil.section_assignee != section_map.get(model_type):
                return queryset.none()

        if profil.niveau_acces == 'REGION' and profil.region_assignee:
            return queryset.filter(eglise__region__icontains=profil.region_assignee)
        elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
            return queryset.filter(eglise__groupe__icontains=profil.groupe_assigne)
        elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
            return queryset.filter(eglise__nom__icontains=profil.district_assigne)

    # ── Finances et Bilans ──────────────────────────────────────────────────
    elif model_type in ['transaction', 'bilan']:
        if profil.niveau_acces == 'REGION' and profil.region_assignee:
            return queryset.filter(eglise__region__icontains=profil.region_assignee)
        elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
            return queryset.filter(eglise__groupe__icontains=profil.groupe_assigne)
        elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
            return queryset.filter(eglise__nom__icontains=profil.district_assigne)

    # Sécurité : aucune correspondance → rien
    return queryset.none()
