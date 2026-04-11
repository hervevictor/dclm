from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from datetime import date

from .models import Retraite, JourRetraite, TYPE_RETRAITE
from .forms import RetraiteForm, JourRetraiteForm
from .exports import export_retraites_pdf, export_retraites_excel
from Eglises.models import Region


# ─── RBAC helpers ─────────────────────────────────────────────────────────────

def _is_national(user):
    if user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.niveau_acces in ['ADMIN', 'COMPTABLE']


def _can_access_region(user, region_name):
    if user.is_superuser:
        return True
    if not hasattr(user, 'profile'):
        return False
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return True
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return p.region_assignee.lower() in region_name.lower()
    return False


def _can_manage(user):
    if user.is_superuser:
        return True
    if not hasattr(user, 'profile'):
        return False
    return user.profile.niveau_acces in ['ADMIN', 'COMPTABLE', 'REGION']


def _filter_retraites(user, qs):
    if user.is_superuser:
        return qs
    if not hasattr(user, 'profile'):
        return qs.none()
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return qs
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return qs.filter(region__name__icontains=p.region_assignee)
    return qs.none()


def _annees_disponibles(qs):
    return sorted(qs.values_list('annee', flat=True).distinct(), reverse=True)


def _compute_totaux(retraites_list):
    """Calcule les totaux depuis une liste de Retraite (avec jours préfetchés)."""
    t = dict(
        total_adultes_h=0, total_adultes_f=0, total_adultes=0,
        total_jeunes_h=0, total_jeunes_f=0, total_jeunes=0,
        total_enfants=0, total_participants=0,
        total_convertis=0, total_eglises=0,
    )
    for r in retraites_list:
        t['total_adultes_h'] += r.adultes_h
        t['total_adultes_f'] += r.adultes_f
        t['total_adultes'] += r.total_adultes
        t['total_jeunes_h'] += r.jeunes_h
        t['total_jeunes_f'] += r.jeunes_f
        t['total_jeunes'] += r.total_jeunes
        t['total_enfants'] += r.enfants
        t['total_participants'] += r.total_participants
        t['total_convertis'] += r.nouveaux_convertis
        t['total_eglises'] += r.nombre_eglises
    return t


# ─── Liste ────────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def retraite_list(request):
    retraites = _filter_retraites(
        request.user,
        Retraite.objects.select_related('region').prefetch_related('jours')
    )
    type_f = request.GET.get('type', '')
    annee_f = request.GET.get('annee', '')
    region_f = request.GET.get('region', '')

    if type_f:
        retraites = retraites.filter(type_retraite=type_f)
    if annee_f:
        retraites = retraites.filter(annee=annee_f)
    if region_f:
        retraites = retraites.filter(region__name__icontains=region_f)
    retraites = retraites.order_by('-annee', 'type_retraite', 'region__name')

    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        parts = []
        if type_f:
            parts.append(dict(TYPE_RETRAITE).get(type_f, type_f))
        if annee_f:
            parts.append(annee_f)
        if region_f:
            parts.append(f'Région {region_f}')
        label = ' — '.join(parts) or 'Toutes les retraites'
        if fmt == 'PDF':
            return export_retraites_pdf(list(retraites), label)
        return export_retraites_excel(list(retraites), label)

    retraites_list = list(retraites)
    totaux = _compute_totaux(retraites_list)
    annees = _annees_disponibles(_filter_retraites(request.user, Retraite.objects.all()))
    all_regions = Region.objects.filter(
        retraites__in=_filter_retraites(request.user, Retraite.objects.all())
    ).distinct().order_by('name')

    return render(request, 'Retraites/retraite_list.html', {
        'retraites': retraites_list,
        'type_choices': TYPE_RETRAITE,
        'annees': annees,
        'all_regions': all_regions,
        'selected_type': type_f,
        'selected_annee': annee_f,
        'selected_region': region_f,
        'peut_ajouter': _can_manage(request.user),
        'is_national': _is_national(request.user),
        **totaux,
    })


# ─── Détail ───────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def retraite_detail(request, pk):
    retraite = get_object_or_404(
        Retraite.objects.select_related('region', 'auteur').prefetch_related('jours__auteur'),
        pk=pk
    )
    if not _can_access_region(request.user, retraite.region.name):
        raise PermissionDenied

    jours = list(retraite.jours.all())
    peut_modifier = _can_manage(request.user)
    peut_supprimer = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )

    # Totaux journaliers pour le pied de tableau
    tot_ah = sum(j.adultes_h for j in jours)
    tot_af = sum(j.adultes_f for j in jours)
    tot_jh = sum(j.jeunes_h for j in jours)
    tot_jf = sum(j.jeunes_f for j in jours)
    tot_enf = sum(j.enfants for j in jours)
    tot_conv = sum(j.nouveaux_convertis for j in jours)

    return render(request, 'Retraites/retraite_detail.html', {
        'retraite': retraite,
        'jours': jours,
        'peut_modifier': peut_modifier,
        'peut_supprimer': peut_supprimer,
        'tot_ah': tot_ah, 'tot_af': tot_af,
        'tot_jh': tot_jh, 'tot_jf': tot_jf,
        'tot_enf': tot_enf, 'tot_conv': tot_conv,
        'tot_participants': tot_ah + tot_af + tot_jh + tot_jf + tot_enf,
    })


# ─── Ajouter retraite ─────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_retraite(request):
    if not _can_manage(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = RetraiteForm(request.POST, user=request.user)
        if form.is_valid():
            r = form.save(commit=False)
            r.auteur = request.user
            r.save()
            messages.success(request, "Retraite créée. Vous pouvez maintenant saisir les rapports journaliers.")
            return redirect('retraite_detail', pk=r.pk)
    else:
        form = RetraiteForm(user=request.user, initial={'annee': date.today().year})
    return render(request, 'Retraites/retraite_form.html', {'form': form, 'action': 'Créer'})


# ─── Modifier retraite ────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def edit_retraite(request, pk):
    retraite = get_object_or_404(Retraite, pk=pk)
    if not (_can_manage(request.user) and _can_access_region(request.user, retraite.region.name)):
        raise PermissionDenied
    if request.method == 'POST':
        form = RetraiteForm(request.POST, instance=retraite, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('retraite_detail', pk=retraite.pk)
    else:
        form = RetraiteForm(instance=retraite, user=request.user)
    return render(request, 'Retraites/retraite_form.html', {
        'form': form, 'action': 'Modifier', 'retraite': retraite,
    })


# ─── Supprimer retraite ───────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def delete_retraite(request, pk):
    retraite = get_object_or_404(Retraite, pk=pk)
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        retraite.delete()
        return redirect('retraite_list')
    return render(request, 'Retraites/retraite_delete.html', {'retraite': retraite})


# ─── Rapport journalier — Ajouter ─────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_jour_retraite(request, retraite_pk):
    retraite = get_object_or_404(
        Retraite.objects.select_related('region').prefetch_related('jours'),
        pk=retraite_pk
    )
    if not (_can_manage(request.user) and _can_access_region(request.user, retraite.region.name)):
        raise PermissionDenied

    if request.method == 'POST':
        form = JourRetraiteForm(request.POST, retraite=retraite)
        if form.is_valid():
            jour = form.save(commit=False)
            jour.retraite = retraite
            jour.auteur = request.user
            jour.save()
            messages.success(request, f"Rapport du {jour.date.strftime('%d/%m/%Y')} enregistré.")
            return redirect('retraite_detail', pk=retraite.pk)
    else:
        # Proposer la prochaine date non encore saisie
        dates_saisies = set(retraite.jours.values_list('date', flat=True))
        from datetime import timedelta
        d = retraite.date_debut
        initial_date = d
        while d in dates_saisies:
            d += timedelta(days=1)
            if retraite.date_fin and d > retraite.date_fin:
                break
            initial_date = d
        form = JourRetraiteForm(retraite=retraite, initial={'date': initial_date})

    return render(request, 'Retraites/jour_retraite_form.html', {
        'form': form,
        'retraite': retraite,
        'action': 'Ajouter',
    })


# ─── Rapport journalier — Modifier ────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def edit_jour_retraite(request, pk):
    jour = get_object_or_404(JourRetraite.objects.select_related('retraite__region'), pk=pk)
    retraite = jour.retraite
    if not (_can_manage(request.user) and _can_access_region(request.user, retraite.region.name)):
        raise PermissionDenied

    if request.method == 'POST':
        form = JourRetraiteForm(request.POST, instance=jour, retraite=retraite)
        if form.is_valid():
            form.save()
            return redirect('retraite_detail', pk=retraite.pk)
    else:
        form = JourRetraiteForm(instance=jour, retraite=retraite)

    return render(request, 'Retraites/jour_retraite_form.html', {
        'form': form,
        'retraite': retraite,
        'jour': jour,
        'action': 'Modifier',
    })


# ─── Rapport journalier — Supprimer ───────────────────────────────────────────

@login_required(login_url='/membres/login/')
def delete_jour_retraite(request, pk):
    jour = get_object_or_404(JourRetraite.objects.select_related('retraite__region'), pk=pk)
    retraite = jour.retraite
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        jour.delete()
        return redirect('retraite_detail', pk=retraite.pk)
    return render(request, 'Retraites/jour_retraite_delete.html', {
        'jour': jour, 'retraite': retraite,
    })


# ─── Rapport par Région ───────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def retraite_region(request, region_name):
    region = get_object_or_404(Region, name=region_name)
    if not _can_access_region(request.user, region_name):
        raise PermissionDenied

    retraites = Retraite.objects.filter(region=region).select_related('region').prefetch_related('jours')
    type_f = request.GET.get('type', '')
    annee_f = request.GET.get('annee', '')
    if type_f:
        retraites = retraites.filter(type_retraite=type_f)
    if annee_f:
        retraites = retraites.filter(annee=annee_f)
    retraites = retraites.order_by('-annee', 'type_retraite')

    retraites_list = list(retraites)

    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        parts = [region.name]
        if type_f:
            parts.append(dict(TYPE_RETRAITE).get(type_f, type_f))
        if annee_f:
            parts.append(annee_f)
        label = ' — '.join(parts)
        if fmt == 'PDF':
            return export_retraites_pdf(retraites_list, label)
        return export_retraites_excel(retraites_list, label)

    totaux = _compute_totaux(retraites_list)
    annees = _annees_disponibles(Retraite.objects.filter(region=region))

    return render(request, 'Retraites/retraite_region.html', {
        'region': region,
        'retraites': retraites_list,
        'type_choices': TYPE_RETRAITE,
        'annees': annees,
        'selected_type': type_f,
        'selected_annee': annee_f,
        'peut_ajouter': _can_manage(request.user),
        **totaux,
    })


# ─── Rapport National ─────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def retraite_national(request):
    if not _is_national(request.user):
        raise PermissionDenied

    type_f = request.GET.get('type', '')
    annee_f = request.GET.get('annee', '')

    qs = Retraite.objects.select_related('region').prefetch_related('jours').all()
    if type_f:
        qs = qs.filter(type_retraite=type_f)
    if annee_f:
        qs = qs.filter(annee=annee_f)

    regions = Region.objects.all().order_by('name')
    all_retraites = list(qs)
    regions_data = []
    for reg in regions:
        rq = [r for r in all_retraites if r.region_id == reg.pk]
        if rq:
            t = _compute_totaux(rq)
            regions_data.append({'region': reg, 'retraites': rq, **t})

    totaux = _compute_totaux(all_retraites)

    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        parts = ['National — TOGO']
        if type_f:
            parts.append(dict(TYPE_RETRAITE).get(type_f, type_f))
        if annee_f:
            parts.append(annee_f)
        label = ' — '.join(parts)
        if fmt == 'PDF':
            return export_retraites_pdf(all_retraites, label)
        return export_retraites_excel(all_retraites, label)

    annees = _annees_disponibles(Retraite.objects.all())

    return render(request, 'Retraites/retraite_national.html', {
        'regions_data': regions_data,
        'type_choices': TYPE_RETRAITE,
        'annees': annees,
        'selected_type': type_f,
        'selected_annee': annee_f,
        **totaux,
    })
