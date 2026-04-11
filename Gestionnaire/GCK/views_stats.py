"""
Vues statistiques de participation aux programmes GCK — avec drill-down.
"""
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum

from .models import BilanGCK, BilanConferenceMinistres, BilanImpact
from Eglises.models import Region, Groupe, Eglise


def _accessible_eglises(user):
    if user.is_superuser:
        return Eglise.objects.all()
    if not hasattr(user, 'profile'):
        return Eglise.objects.none()
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return Eglise.objects.all()
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return Eglise.objects.filter(region__icontains=p.region_assignee)
    if p.niveau_acces == 'GROUPE' and p.groupe_assigne:
        return Eglise.objects.filter(groupe__icontains=p.groupe_assigne)
    if p.niveau_acces == 'DISTRICT' and p.district_assigne:
        return Eglise.objects.filter(nom__icontains=p.district_assigne)
    return Eglise.objects.none()


def _sum_programme(model, eglise_pks, annee=None):
    qs = model.objects.filter(eglise_id__in=eglise_pks)
    if annee:
        qs = qs.filter(date__year=annee)
    agg = qs.aggregate(
        ah=Sum('adultes_hommes'), af=Sum('adultes_femmes'),
        jh=Sum('jeunes_hommes'),  jf=Sum('jeunes_femmes'),
        enf=Sum('enfants'),
    )
    ah = agg['ah'] or 0; af = agg['af'] or 0
    jh = agg['jh'] or 0; jf = agg['jf'] or 0
    enf = agg['enf'] or 0
    return ah + af, jh + jf, enf, ah + af + jh + jf + enf


def _row(pks, annee):
    ga, gj, ge, gt = _sum_programme(BilanGCK,                  pks, annee)
    ca, cj, ce, ct = _sum_programme(BilanConferenceMinistres,   pks, annee)
    ia, ij, ie, it = _sum_programme(BilanImpact,                pks, annee)
    return {
        'gck_total': gt,   'conf_total': ct,   'impact_total': it,
        'gck_adultes': ga, 'gck_jeunes': gj,   'gck_enfants': ge,
        'conf_adultes': ca,'conf_jeunes': cj,   'conf_enfants': ce,
        'imp_adultes': ia, 'imp_jeunes': ij,   'imp_enfants': ie,
        'grand_total': gt + ct + it,
    }


# ─── API AJAX — Drill-down GCK ────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def stats_gck_api(request):
    """
    level=region            → toutes les régions
    level=groupe&parent=X   → groupes de la région X
    level=district&parent=X → districts du groupe X
    """
    level  = request.GET.get('level', 'region')
    parent = request.GET.get('parent', '')
    annee  = request.GET.get('annee', '')
    annee_int = int(annee) if annee.isdigit() else None
    acc = _accessible_eglises(request.user)

    items = []

    if level == 'region':
        for region in Region.objects.order_by('name'):
            pks = list(acc.filter(region__icontains=region.name).values_list('pk', flat=True))
            if not pks:
                continue
            d = _row(pks, annee_int)
            if d['grand_total'] == 0:
                continue
            items.append({'label': region.name, **d})

    elif level == 'groupe':
        for groupe in Groupe.objects.filter(region__icontains=parent).order_by('name'):
            pks = list(acc.filter(groupe__icontains=groupe.name).values_list('pk', flat=True))
            if not pks:
                continue
            d = _row(pks, annee_int)
            if d['grand_total'] == 0:
                continue
            items.append({'label': groupe.name, **d})

    elif level == 'district':
        for eg in acc.filter(groupe__icontains=parent).order_by('nom'):
            d = _row([eg.pk], annee_int)
            if d['grand_total'] == 0:
                continue
            items.append({'label': eg.nom, **d})

    else:
        return JsonResponse({'error': 'Niveau inconnu.'}, status=400)

    def col(key): return [i[key] for i in items]

    return JsonResponse({
        'labels':       col('label'),
        'gck_total':    col('gck_total'),
        'conf_total':   col('conf_total'),
        'impact_total': col('impact_total'),
        'gck_adultes':  col('gck_adultes'),
        'gck_jeunes':   col('gck_jeunes'),
        'gck_enfants':  col('gck_enfants'),
        'conf_adultes': col('conf_adultes'),
        'conf_jeunes':  col('conf_jeunes'),
        'conf_enfants': col('conf_enfants'),
        'imp_adultes':  col('imp_adultes'),
        'imp_jeunes':   col('imp_jeunes'),
        'imp_enfants':  col('imp_enfants'),
        'grand_totals': col('grand_total'),
    })


# ─── Page principale ──────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def stats_gck(request):
    acc = _accessible_eglises(request.user)
    annees = sorted(set(
        list(BilanGCK.objects.values_list('date__year', flat=True).distinct()) +
        list(BilanConferenceMinistres.objects.values_list('date__year', flat=True).distinct()) +
        list(BilanImpact.objects.values_list('date__year', flat=True).distinct())
    ), reverse=True)

    regions = list(Region.objects.all().order_by('name').values_list('name', flat=True))
    groupes_par_region = {}
    for r in regions:
        pks = list(acc.filter(region__icontains=r).values_list('pk', flat=True))
        grps = list(Groupe.objects.filter(region__icontains=r).order_by('name').values_list('name', flat=True))
        if pks and grps:
            groupes_par_region[r] = grps

    return render(request, 'GCK/stats_gck.html', {
        'annees': annees,
        'selected_annee': request.GET.get('annee', ''),
        'regions_json': json.dumps(regions, ensure_ascii=False),
        'groupes_json': json.dumps(groupes_par_region, ensure_ascii=False),
    })
