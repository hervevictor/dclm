"""Vues pour la Conférence des Ministres (séances du matin lors des GCK)."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .models import BilanConferenceMinistres
from .forms import BilanConferenceMinistresForm
from .resources import BilanConferenceMinistresResource
from .views import (
    MOIS_FR, _apply_date_filters, _compute_totaux,
    _export_label, _export_section_bilans,
)
from Eglises.models import Eglise, Groupe, Region
from Eglises.templatetags.region_labels import get_labels
from Membres.utils import filter_by_rbac, RBACMixin, AdminOnlyMixin

_SECTION_TITLE = "Conférence des Ministres (GCK — Matin)"
_TEMPLATE_PREFIX = "GCK/conference"


def _export(bilans, totaux, fmt, label):
    return _export_section_bilans(
        bilans, totaux, fmt,
        BilanConferenceMinistresResource, 'conference_rapport',
        _SECTION_TITLE, label,
    )


# ─── Liste ────────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_list(request):
    bilans = BilanConferenceMinistres.objects.all()
    bilans = filter_by_rbac(request.user, bilans, 'bilan')

    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    district = request.GET.get('district', '')

    if region:
        bilans = bilans.filter(eglise__region__icontains=region)
    if groupe:
        bilans = bilans.filter(eglise__groupe__icontains=groupe)
    if district:
        bilans = bilans.filter(eglise__nom__icontains=district)

    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)
    bilans = bilans.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')
    totaux = _compute_totaux(bilans)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        label = _export_label(region, groupe, district, start_date, end_date, mois, jour, '')
        return _export(bilans, totaux, fmt, label)

    all_eglises = filter_by_rbac(request.user, Eglise.objects.all(), 'eglise').order_by('nom')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')
    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')

    return render(request, f'{_TEMPLATE_PREFIX}_list.html', {
        'bilans': bilans,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        'all_eglises': all_eglises, 'all_groupes': all_groupes, 'all_regions': all_regions,
        'selected_region': region, 'selected_groupe': groupe, 'selected_district': district,
        **totaux,
    })


# ─── Ajouter ──────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_conference(request):
    user = request.user
    avertissement = None
    district_unique = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        district_unique = user.profile.district_assigne

    if request.method == 'POST':
        form = BilanConferenceMinistresForm(request.POST, user=user)
        if form.is_valid():
            eglise_choisie = form.cleaned_data['eglise']
            if district_unique and district_unique.lower() not in eglise_choisie.nom.lower():
                avertissement = f"Attention : vous avez soumis un rapport pour « {eglise_choisie.nom} » alors que votre district assigné est « {district_unique} »."
            bilan = form.save()
            return redirect('conference_detail', pk=bilan.pk)
    else:
        form = BilanConferenceMinistresForm(user=user)

    return render(request, f'{_TEMPLATE_PREFIX}_add.html', {
        'form': form,
        'avertissement': avertissement,
        'district_unique': district_unique,
    })


# ─── Détail ───────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_detail(request, pk):
    bilan = get_object_or_404(BilanConferenceMinistres, pk=pk)
    from Eglises.views import can_edit_eglise
    peut_modifier = can_edit_eglise(request.user, bilan.eglise)
    peut_supprimer = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )
    return render(request, f'{_TEMPLATE_PREFIX}_detail.html', {
        'bilan': bilan,
        'peut_modifier': peut_modifier,
        'peut_supprimer': peut_supprimer,
    })


# ─── Modifier ─────────────────────────────────────────────────────────────────

class EditConference(RBACMixin, UpdateView):
    model = BilanConferenceMinistres
    form_class = BilanConferenceMinistresForm
    template_name = f'{_TEMPLATE_PREFIX}_edit.html'

    def dispatch(self, request, *args, **kwargs):
        bilan = self.get_object()
        from Eglises.views import can_edit_eglise
        if not can_edit_eglise(request.user, bilan.eglise):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('conference_detail', kwargs={'pk': self.object.pk})


# ─── Supprimer ────────────────────────────────────────────────────────────────

class DeleteConference(AdminOnlyMixin, DeleteView):
    model = BilanConferenceMinistres
    template_name = f'{_TEMPLATE_PREFIX}_delete.html'
    success_url = reverse_lazy('conference_list')


# ─── Rapport par District ─────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_district(request, dist_pk):
    eglise = get_object_or_404(Eglise, pk=dist_pk)
    bilans = BilanConferenceMinistres.objects.filter(eglise=eglise)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        totaux = _compute_totaux(bilans)
        label = f"{eglise.nom} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export(bilans, totaux, request.POST.get('file-format'), label)

    bilans = bilans.order_by('-date')
    totaux = _compute_totaux(bilans)
    return render(request, f'{_TEMPLATE_PREFIX}_district.html', {
        'eglise': eglise, 'bilans': bilans, 'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    })


# ─── Rapport par Groupe ───────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    lbl = get_labels(groupe.region)
    bilans = BilanConferenceMinistres.objects.filter(eglise__groupe=group)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        totaux = _compute_totaux(bilans)
        label = f"{groupe.name} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export(bilans, totaux, request.POST.get('file-format'), label)

    bilans = bilans.order_by('eglise__nom', '-date')
    totaux = _compute_totaux(bilans)
    return render(request, f'{_TEMPLATE_PREFIX}_groupe.html', {
        'groupe': groupe, 'lbl': lbl, 'bilans': bilans, 'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    })


# ─── Rapport par Région ───────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    lbl = get_labels(region.name)
    bilans = BilanConferenceMinistres.objects.filter(eglise__region=regs)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        totaux = _compute_totaux(bilans)
        label = f"{region.name} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export(bilans, totaux, request.POST.get('file-format'), label)

    bilans = bilans.order_by('eglise__groupe', 'eglise__nom', '-date')
    totaux = _compute_totaux(bilans)
    return render(request, f'{_TEMPLATE_PREFIX}_region.html', {
        'region': region, 'lbl': lbl, 'bilans': bilans, 'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    })


# ─── Rapport National ─────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def conference_national(request):
    bilans = BilanConferenceMinistres.objects.all()
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        totaux = _compute_totaux(bilans)
        label = f"National — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export(bilans, totaux, request.POST.get('file-format'), label)

    bilans = bilans.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')
    totaux = _compute_totaux(bilans)

    regions = Region.objects.all().order_by('name')
    regions_data = []
    for r in regions:
        b = bilans.filter(eglise__region=r.name)
        t = _compute_totaux(b)
        if b.exists():
            regions_data.append({'region': r, 'bilan_count': b.count(), **t})

    return render(request, f'{_TEMPLATE_PREFIX}_national.html', {
        'bilans': bilans, 'bilan_count': bilans.count(),
        'regions_data': regions_data,
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    })
