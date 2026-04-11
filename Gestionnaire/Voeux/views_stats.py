"""
Vues statistiques pour Voeux, Contributions, et suivi individuel d'un membre.
"""
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Sum

from .models import Voeu, Contribution, VersementVoeu, VersementContribution
from Eglises.models import Region, Groupe, Eglise
from Adultes.models import Adulte


# ─── RBAC helper ──────────────────────────────────────────────────────────────

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


# ─── Agrégation Voeux + Contributions ────────────────────────────────────────

def _aggregate_voeux_contrib(eglise_pks):
    """(promis_voeux, paye_voeux, objectif_contrib, paye_contrib)"""
    voeux_qs = Voeu.objects.filter(eglise_id__in=eglise_pks)
    promis  = voeux_qs.aggregate(s=Sum('montant_promis'))['s'] or 0
    premier = voeux_qs.aggregate(s=Sum('premier_versement'))['s'] or 0
    vers_v  = VersementVoeu.objects.filter(voeu__eglise_id__in=eglise_pks).aggregate(s=Sum('montant'))['s'] or 0

    contrib_qs = Contribution.objects.filter(eglise_id__in=eglise_pks)
    objectif   = contrib_qs.aggregate(s=Sum('montant_objectif'))['s'] or 0
    vers_c     = VersementContribution.objects.filter(contribution__eglise_id__in=eglise_pks).aggregate(s=Sum('montant'))['s'] or 0

    return promis, premier + vers_v, objectif, vers_c


def _aggregate_voeux_contrib_membre(adulte):
    """Agrégation pour un membre individuel."""
    voeux_qs = Voeu.objects.filter(membre=adulte)
    promis  = voeux_qs.aggregate(s=Sum('montant_promis'))['s'] or 0
    premier = voeux_qs.aggregate(s=Sum('premier_versement'))['s'] or 0
    vers_v  = VersementVoeu.objects.filter(voeu__membre=adulte).aggregate(s=Sum('montant'))['s'] or 0

    contribs = Contribution.objects.filter(membre=adulte)
    objectif = contribs.aggregate(s=Sum('montant_objectif'))['s'] or 0
    vers_c   = VersementContribution.objects.filter(contribution__membre=adulte).aggregate(s=Sum('montant'))['s'] or 0

    return promis, premier + vers_v, objectif, vers_c


# ─── API AJAX — Drill-down Voeux/Contributions ────────────────────────────────

@login_required(login_url='/membres/login/')
def stats_voeux_api(request):
    """
    level=region              → toutes les régions accessibles
    level=groupe&parent=X     → groupes de la région X
    level=district&parent=X   → districts du groupe X
    level=membre&parent=X     → membres du district X (superadmin only)
    """
    level  = request.GET.get('level', 'region')
    parent = request.GET.get('parent', '')
    acc    = _accessible_eglises(request.user)

    labels, pv_list, ppv_list, oc_list, pc_list, pks_list = [], [], [], [], [], []

    if level == 'region':
        for region in Region.objects.order_by('name'):
            pks = list(acc.filter(region__icontains=region.name).values_list('pk', flat=True))
            if not pks:
                continue
            p, pv, o, pc = _aggregate_voeux_contrib(pks)
            if p == pv == o == pc == 0:
                continue
            labels.append(region.name)
            pv_list.append(p); ppv_list.append(pv); oc_list.append(o); pc_list.append(pc)
            pks_list.append(None)

    elif level == 'groupe':
        for groupe in Groupe.objects.filter(region__icontains=parent).order_by('name'):
            pks = list(acc.filter(groupe__icontains=groupe.name).values_list('pk', flat=True))
            if not pks:
                continue
            p, pv, o, pc = _aggregate_voeux_contrib(pks)
            if p == pv == o == pc == 0:
                continue
            labels.append(groupe.name)
            pv_list.append(p); ppv_list.append(pv); oc_list.append(o); pc_list.append(pc)
            pks_list.append(None)

    elif level == 'district':
        for eg in acc.filter(groupe__icontains=parent).order_by('nom'):
            p, pv, o, pc = _aggregate_voeux_contrib([eg.pk])
            if p == pv == o == pc == 0:
                continue
            labels.append(eg.nom)
            pv_list.append(p); ppv_list.append(pv); oc_list.append(o); pc_list.append(pc)
            pks_list.append(None)

    elif level == 'membre':
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Réservé au superadmin.'}, status=403)
        eglise = acc.filter(nom__icontains=parent).first()
        if eglise:
            for adulte in Adulte.objects.filter(eglise=eglise).order_by('nom', 'prenom'):
                p, pv, o, pc = _aggregate_voeux_contrib_membre(adulte)
                if p == pv == o == pc == 0:
                    continue
                labels.append(f"{adulte.nom} {adulte.prenom}")
                pv_list.append(p); ppv_list.append(pv); oc_list.append(o); pc_list.append(pc)
                pks_list.append(adulte.pk)
    else:
        return JsonResponse({'error': 'Niveau inconnu.'}, status=400)

    return JsonResponse({
        'labels':            labels,
        'promis_voeux':      pv_list,
        'paye_voeux':        ppv_list,
        'objectif_contrib':  oc_list,
        'paye_contrib':      pc_list,
        'adulte_pks':        pks_list,
    })


# ─── Page principale ──────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def stats_voeux_contributions(request):
    acc = _accessible_eglises(request.user)
    regions = list(Region.objects.all().order_by('name').values_list('name', flat=True))

    # Groupes par région pour les dropdowns
    groupes_par_region = {}
    for r in regions:
        eglise_pks = list(acc.filter(region__icontains=r).values_list('pk', flat=True))
        grps = list(Groupe.objects.filter(region__icontains=r).order_by('name').values_list('name', flat=True))
        if eglise_pks and grps:
            groupes_par_region[r] = grps

    return render(request, 'Voeux/stats_voeux.html', {
        'is_superadmin': request.user.is_superuser,
        'regions_json': json.dumps(regions, ensure_ascii=False),
        'groupes_json': json.dumps(groupes_par_region, ensure_ascii=False),
    })


# ─── Suivi individuel d'un membre ─────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def stats_membre(request, adulte_pk):
    adulte = get_object_or_404(Adulte.objects.select_related('eglise'), pk=adulte_pk)
    acc = _accessible_eglises(request.user)
    if not acc.filter(pk=adulte.eglise_id).exists():
        raise PermissionDenied

    voeux = Voeu.objects.filter(membre=adulte).prefetch_related('versements').order_by('date_voeu')
    voeux_labels, voeux_promis, voeux_paye, voeux_restant = [], [], [], []
    for v in voeux:
        voeux_labels.append(v.date_voeu.strftime('%d/%m/%Y'))
        voeux_promis.append(v.montant_promis)
        paye = v.total_paye
        voeux_paye.append(paye)
        voeux_restant.append(max(0, v.montant_promis - paye))

    contribs = (Contribution.objects.filter(membre=adulte)
                .select_related('type_contribution').prefetch_related('versements')
                .order_by('date_contribution'))
    contrib_labels, contrib_obj, contrib_verse, contrib_restant = [], [], [], []
    for c in contribs:
        nom_type = c.type_contribution.nom if c.type_contribution else '—'
        contrib_labels.append(f"{nom_type}\n({c.date_contribution.strftime('%d/%m/%Y')})")
        obj = c.montant_objectif or 0
        verse = c.total_verse
        contrib_obj.append(obj)
        contrib_verse.append(verse)
        contrib_restant.append(max(0, obj - verse))

    return render(request, 'Voeux/stats_membre.html', {
        'adulte': adulte,
        'voeux_data': json.dumps({
            'labels': voeux_labels, 'promis': voeux_promis,
            'paye': voeux_paye, 'restant': voeux_restant,
        }, ensure_ascii=False),
        'contrib_data': json.dumps({
            'labels': contrib_labels, 'objectif': contrib_obj,
            'verse': contrib_verse, 'restant': contrib_restant,
        }, ensure_ascii=False),
        'has_voeux':   bool(voeux),
        'has_contribs': bool(contribs),
        'total_promis':     sum(voeux_promis),
        'total_paye_voeux': sum(voeux_paye),
        'total_obj':   sum(contrib_obj),
        'total_verse': sum(contrib_verse),
    })
