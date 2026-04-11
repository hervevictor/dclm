from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import date as dt_date, timedelta

from .models import (TypeContribution, Voeu, VersementVoeu, Contribution,
                     VersementContribution, HistoriqueVoeu, HistoriqueContribution,
                     HistoriqueVersementVoeu, HistoriqueVersementContribution)
from .forms import (VoeuForm, VersementVoeuForm, ContributionForm,
                    VersementContributionForm, TypeContributionForm,
                    ModifierMontantVoeuForm, ModifierMontantContributionForm,
                    CorrectionVersementForm)
from .exports import export_voeux, export_contributions
from Eglises.models import Eglise, Groupe, Region
from Adultes.models import Adulte
from Membres.utils import filter_by_rbac, admin_required


# ─── Helper RBAC ──────────────────────────────────────────────────────────────

def _filter_voeux(user, qs):
    return filter_by_rbac(user, qs, 'bilan')  # eglise__ same path


def _filter_contribs(user, qs):
    return filter_by_rbac(user, qs, 'bilan')


def _is_admin_national(user):
    """Superadmin ou dirigeant national (niveau ADMIN)."""
    if user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.niveau_acces == 'ADMIN'


def _can_modifier_montant(user, auteur):
    """Seul l'auteur de la saisie (compte lié à l'église) peut modifier le montant.
    Les superusers et admins peuvent aussi le faire."""
    if user.is_superuser:
        return True
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'ADMIN':
        return True
    return auteur is not None and user.pk == auteur.pk


def _can_manage(user, eglise):
    """Peut-on saisir/modifier pour cette église ?"""
    if user.is_superuser:
        return True
    if not hasattr(user, 'profile'):
        return False
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return True
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return p.region_assignee.lower() in eglise.region.lower()
    if p.niveau_acces == 'GROUPE' and p.groupe_assigne:
        return p.groupe_assigne.lower() in eglise.groupe.lower()
    if p.niveau_acces == 'DISTRICT' and p.district_assigne:
        return p.district_assigne.lower() in eglise.nom.lower()
    return False


# ─── AJAX : membres par église ─────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def membres_par_eglise(request, eglise_pk):
    """Retourne la liste JSON des membres (Adultes) d'une église."""
    eglise = get_object_or_404(Eglise, pk=eglise_pk)
    if not _can_manage(request.user, eglise):
        return JsonResponse({'membres': []})
    membres = Adulte.objects.filter(eglise=eglise).order_by('nom', 'prenom')
    data = [{'id': m.pk, 'text': str(m)} for m in membres]
    return JsonResponse({'membres': data})


# ════════════════════════════════════════════════════════════════════════════
# VOEUX
# ════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/membres/login/')
def voeu_list(request):
    voeux = _filter_voeux(request.user, Voeu.objects.select_related('membre', 'eglise'))

    # Filtres
    eglise_pk = request.GET.get('eglise', '')
    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    solde = request.GET.get('solde', '')  # 'oui' / 'non'

    if eglise_pk:
        voeux = voeux.filter(eglise_id=eglise_pk)
    if region:
        voeux = voeux.filter(eglise__region__icontains=region)
    if groupe:
        voeux = voeux.filter(eglise__groupe__icontains=groupe)

    voeux = voeux.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', 'membre__nom')

    # Export
    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        label_parts = []
        if region: label_parts.append(f'Région {region}')
        if groupe: label_parts.append(f'Groupe {groupe}')
        if eglise_pk: label_parts.append(f'Église #{eglise_pk}')
        label = ' — '.join(label_parts) or 'Tous les voeux'
        return export_voeux(voeux, fmt, label)

    # Totaux
    agg = voeux.aggregate(
        total_promis=Sum('montant_promis'),
    )
    total_promis = agg['total_promis'] or 0
    total_paye = sum(v.total_paye for v in voeux)
    total_restant = sum(v.montant_restant for v in voeux)

    all_eglises = filter_by_rbac(request.user, Eglise.objects.all(), 'eglise').order_by('nom')
    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')

    return render(request, 'Voeux/voeu_list.html', {
        'voeux': voeux,
        'total_promis': total_promis,
        'total_paye': total_paye,
        'total_restant': total_restant,
        'voeu_count': voeux.count(),
        'all_eglises': all_eglises,
        'all_regions': all_regions,
        'all_groupes': all_groupes,
        'selected_eglise': eglise_pk,
        'selected_region': region,
        'selected_groupe': groupe,
    })


@login_required(login_url='/membres/login/')
def add_voeu(request):
    user = request.user
    # Pré-remplir l'église si DISTRICT
    eglise_defaut = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        e = Eglise.objects.filter(nom__icontains=user.profile.district_assigne).first()
        if e:
            eglise_defaut = e

    if request.method == 'POST':
        form = VoeuForm(request.POST, user=user)
        if form.is_valid():
            voeu = form.save()
            # Si premier versement > 0, créer automatiquement le VersementVoeu
            if voeu.premier_versement > 0:
                VersementVoeu.objects.create(
                    voeu=voeu,
                    montant=voeu.premier_versement,
                    date=voeu.date_voeu,
                    auteur=user,
                    notes="Premier versement enregistré à la création du voeu",
                )
            return redirect('voeu_detail', pk=voeu.pk)
    else:
        initial = {}
        if eglise_defaut:
            initial['eglise'] = eglise_defaut.pk
        form = VoeuForm(user=user, initial=initial)

    return render(request, 'Voeux/voeu_add.html', {
        'form': form,
        'eglise_defaut': eglise_defaut,
    })


@login_required(login_url='/membres/login/')
def voeu_detail(request, pk):
    voeu = get_object_or_404(Voeu.objects.select_related('membre', 'eglise', 'auteur'), pk=pk)
    if not _can_manage(request.user, voeu.eglise):
        raise PermissionDenied
    versements = voeu.versements.select_related('auteur').all()
    is_admin = _is_admin_national(request.user)
    peut_modifier = _can_manage(request.user, voeu.eglise)
    peut_supprimer = is_admin
    peut_modifier_montant = _can_modifier_montant(request.user, voeu.auteur)
    user_pk = request.user.pk
    versements_corrigeables = {v.pk for v in versements if is_admin or v.auteur_id == user_pk}

    seuil_7j = timezone.now() - timedelta(days=7)
    all_historiques = voeu.historiques.select_related('auteur').all()
    historiques = all_historiques.filter(created__gte=seuil_7j)
    historiques_masques = all_historiques.filter(created__lt=seuil_7j).count()

    all_vc = HistoriqueVersementVoeu.objects.filter(
        versement__voeu=voeu).select_related('auteur', 'versement')
    versement_corrections = all_vc.filter(created__gte=seuil_7j)
    vc_masques = all_vc.filter(created__lt=seuil_7j).count()

    return render(request, 'Voeux/voeu_detail.html', {
        'voeu': voeu,
        'versements': versements,
        'historiques': historiques,
        'historiques_masques': historiques_masques,
        'versement_corrections': versement_corrections,
        'vc_masques': vc_masques,
        'peut_modifier': peut_modifier,
        'peut_supprimer': peut_supprimer,
        'peut_modifier_montant': peut_modifier_montant,
        'versements_corrigeables': versements_corrigeables,
        'is_admin': is_admin,
    })


@login_required(login_url='/membres/login/')
def edit_voeu(request, pk):
    voeu = get_object_or_404(Voeu, pk=pk)
    if not _can_manage(request.user, voeu.eglise):
        raise PermissionDenied
    if request.method == 'POST':
        form = VoeuForm(request.POST, instance=voeu, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('voeu_detail', pk=voeu.pk)
    else:
        form = VoeuForm(instance=voeu, user=request.user)
    return render(request, 'Voeux/voeu_edit.html', {'form': form, 'voeu': voeu})


@login_required(login_url='/membres/login/')
def delete_voeu(request, pk):
    voeu = get_object_or_404(Voeu, pk=pk)
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        voeu.delete()
        return redirect('voeu_list')
    return render(request, 'Voeux/voeu_delete.html', {'voeu': voeu})


@login_required(login_url='/membres/login/')
def add_versement_voeu(request, voeu_pk):
    voeu = get_object_or_404(Voeu.objects.select_related('membre', 'eglise'), pk=voeu_pk)
    if not _can_manage(request.user, voeu.eglise):
        raise PermissionDenied
    if request.method == 'POST':
        form = VersementVoeuForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.voeu = voeu
            v.auteur = request.user
            v.save()
            return redirect('voeu_detail', pk=voeu.pk)
    else:
        form = VersementVoeuForm(initial={'date': dt_date.today(), 'auteur': request.user.pk})
    return render(request, 'Voeux/versement_voeu_add.html', {'form': form, 'voeu': voeu})


@login_required(login_url='/membres/login/')
def delete_versement_voeu(request, pk):
    v = get_object_or_404(VersementVoeu, pk=pk)
    voeu_pk = v.voeu_id
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        v.delete()
        return redirect('voeu_detail', pk=voeu_pk)
    return render(request, 'Voeux/versement_voeu_delete.html', {'versement': v})


# ─── Hiérarchie Voeux ─────────────────────────────────────────────────────────

def _voeux_stats(voeux_qs):
    """Calcule les stats d'un queryset de voeux (requires evaluated)."""
    voeux_list = list(voeux_qs)
    total_promis = sum(v.montant_promis for v in voeux_list)
    total_paye = sum(v.total_paye for v in voeux_list)
    total_restant = sum(v.montant_restant for v in voeux_list)
    return total_promis, total_paye, total_restant


@login_required(login_url='/membres/login/')
def voeu_district(request, eglise_pk):
    eglise = get_object_or_404(Eglise, pk=eglise_pk)
    if not _can_manage(request.user, eglise):
        raise PermissionDenied
    voeux = Voeu.objects.filter(eglise=eglise).select_related('membre')
    voeux = voeux.order_by('membre__nom', 'membre__prenom')
    total_promis, total_paye, total_restant = _voeux_stats(voeux)
    return render(request, 'Voeux/voeu_district.html', {
        'eglise': eglise,
        'voeux': voeux,
        'voeu_count': voeux.count(),
        'total_promis': total_promis,
        'total_paye': total_paye,
        'total_restant': total_restant,
    })


@login_required(login_url='/membres/login/')
def voeu_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            e = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not e or e.groupe != group:
                raise PermissionDenied
    voeux = _filter_voeux(request.user, Voeu.objects.filter(eglise__groupe=group))

    eglises = Eglise.objects.filter(groupe=group).order_by('nom')
    eglises_data = []
    for e in eglises:
        vq = voeux.filter(eglise=e).select_related('membre').order_by('membre__nom')
        tp, tpy, tr = _voeux_stats(vq)
        if vq.exists():
            eglises_data.append({
                'eglise': e, 'voeux': vq, 'count': vq.count(),
                'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
            })

    tp, tpy, tr = _voeux_stats(voeux)
    return render(request, 'Voeux/voeu_groupe.html', {
        'groupe': groupe,
        'eglises_data': eglises_data,
        'voeu_count': voeux.count(),
        'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
    })


@login_required(login_url='/membres/login/')
def voeu_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            e = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not e or e.region != regs:
                raise PermissionDenied
        elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
            e = Eglise.objects.filter(groupe__icontains=p.groupe_assigne).first()
            if not e or e.region != regs:
                raise PermissionDenied
    voeux = _filter_voeux(request.user, Voeu.objects.filter(eglise__region=regs))

    groupes = Groupe.objects.filter(region=regs).order_by('name')
    groupes_data = []
    for g in groupes:
        vq = voeux.filter(eglise__groupe=g.name)
        tp, tpy, tr = _voeux_stats(vq)
        if vq.exists():
            groupes_data.append({
                'groupe': g, 'count': vq.count(),
                'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
            })

    tp, tpy, tr = _voeux_stats(voeux)
    return render(request, 'Voeux/voeu_region.html', {
        'region': region,
        'groupes_data': groupes_data,
        'voeu_count': voeux.count(),
        'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
    })


@login_required(login_url='/membres/login/')
def voeu_national(request):
    if not _is_admin_national(request.user):
        raise PermissionDenied
    voeux = _filter_voeux(request.user, Voeu.objects.all())
    regions = Region.objects.all().order_by('name')
    regions_data = []
    for r in regions:
        vq = voeux.filter(eglise__region=r.name)
        tp, tpy, tr = _voeux_stats(vq)
        if vq.exists():
            regions_data.append({
                'region': r, 'count': vq.count(),
                'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
            })
    tp, tpy, tr = _voeux_stats(voeux)
    return render(request, 'Voeux/voeu_national.html', {
        'regions_data': regions_data,
        'voeu_count': voeux.count(),
        'total_promis': tp, 'total_paye': tpy, 'total_restant': tr,
    })


# ════════════════════════════════════════════════════════════════════════════
# CONTRIBUTIONS
# ════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/membres/login/')
def contribution_list(request):
    contribs = _filter_contribs(request.user, Contribution.objects.select_related('membre', 'eglise', 'type_contribution'))

    eglise_pk = request.GET.get('eglise', '')
    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    type_pk = request.GET.get('type', '')

    if eglise_pk:
        contribs = contribs.filter(eglise_id=eglise_pk)
    if region:
        contribs = contribs.filter(eglise__region__icontains=region)
    if groupe:
        contribs = contribs.filter(eglise__groupe__icontains=groupe)
    if type_pk:
        contribs = contribs.filter(type_contribution_id=type_pk)

    contribs = contribs.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', 'membre__nom')

    # Export
    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        label_parts = []
        if region: label_parts.append(f'Région {region}')
        if groupe: label_parts.append(f'Groupe {groupe}')
        if eglise_pk: label_parts.append(f'Église #{eglise_pk}')
        if type_pk: label_parts.append(f'Type #{type_pk}')
        label = ' — '.join(label_parts) or 'Toutes les contributions'
        return export_contributions(contribs, fmt, label)

    total_objectif = sum(c.montant_objectif or 0 for c in contribs)
    total_verse = sum(c.total_verse for c in contribs)

    all_eglises = filter_by_rbac(request.user, Eglise.objects.all(), 'eglise').order_by('nom')
    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')
    all_types = TypeContribution.objects.filter(actif=True)

    return render(request, 'Voeux/contribution_list.html', {
        'contribs': contribs,
        'total_objectif': total_objectif,
        'total_verse': total_verse,
        'contrib_count': contribs.count(),
        'all_eglises': all_eglises,
        'all_regions': all_regions,
        'all_groupes': all_groupes,
        'all_types': all_types,
        'selected_eglise': eglise_pk,
        'selected_region': region,
        'selected_groupe': groupe,
        'selected_type': type_pk,
    })


@login_required(login_url='/membres/login/')
def add_contribution(request):
    user = request.user
    eglise_defaut = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        e = Eglise.objects.filter(nom__icontains=user.profile.district_assigne).first()
        if e:
            eglise_defaut = e

    if request.method == 'POST':
        form = ContributionForm(request.POST, user=user)
        if form.is_valid():
            contrib = form.save()
            return redirect('contribution_detail', pk=contrib.pk)
    else:
        initial = {}
        if eglise_defaut:
            initial['eglise'] = eglise_defaut.pk
        form = ContributionForm(user=user, initial=initial)

    return render(request, 'Voeux/contribution_add.html', {
        'form': form,
        'eglise_defaut': eglise_defaut,
    })


@login_required(login_url='/membres/login/')
def contribution_detail(request, pk):
    contrib = get_object_or_404(
        Contribution.objects.select_related('membre', 'eglise', 'type_contribution', 'auteur'), pk=pk)
    if not _can_manage(request.user, contrib.eglise):
        raise PermissionDenied
    versements = contrib.versements.select_related('auteur').all()
    is_admin = _is_admin_national(request.user)
    peut_modifier = _can_manage(request.user, contrib.eglise)
    peut_supprimer = is_admin
    user_pk = request.user.pk
    versements_corrigeables = {v.pk for v in versements if is_admin or v.auteur_id == user_pk}

    seuil_7j = timezone.now() - timedelta(days=7)
    all_historiques = contrib.historiques.select_related('auteur').all()
    historiques = all_historiques.filter(created__gte=seuil_7j)
    historiques_masques = all_historiques.filter(created__lt=seuil_7j).count()

    all_vc = HistoriqueVersementContribution.objects.filter(
        versement__contribution=contrib).select_related('auteur', 'versement')
    versement_corrections = all_vc.filter(created__gte=seuil_7j)
    vc_masques = all_vc.filter(created__lt=seuil_7j).count()

    return render(request, 'Voeux/contribution_detail.html', {
        'contrib': contrib,
        'versements': versements,
        'historiques': historiques,
        'historiques_masques': historiques_masques,
        'versement_corrections': versement_corrections,
        'vc_masques': vc_masques,
        'peut_modifier': peut_modifier,
        'peut_supprimer': peut_supprimer,
        'versements_corrigeables': versements_corrigeables,
        'is_admin': is_admin,
    })


@login_required(login_url='/membres/login/')
def edit_contribution(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk)
    if not _can_manage(request.user, contrib.eglise):
        raise PermissionDenied
    if request.method == 'POST':
        form = ContributionForm(request.POST, instance=contrib, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('contribution_detail', pk=contrib.pk)
    else:
        form = ContributionForm(instance=contrib, user=request.user)
    return render(request, 'Voeux/contribution_edit.html', {'form': form, 'contrib': contrib})


@login_required(login_url='/membres/login/')
def delete_contribution(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk)
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        contrib.delete()
        return redirect('contribution_list')
    return render(request, 'Voeux/contribution_delete.html', {'contrib': contrib})


@login_required(login_url='/membres/login/')
def add_versement_contribution(request, contrib_pk):
    contrib = get_object_or_404(Contribution.objects.select_related('membre', 'eglise'), pk=contrib_pk)
    if not _can_manage(request.user, contrib.eglise):
        raise PermissionDenied
    if request.method == 'POST':
        form = VersementContributionForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.contribution = contrib
            v.auteur = request.user
            v.save()
            return redirect('contribution_detail', pk=contrib.pk)
    else:
        form = VersementContributionForm(initial={'date': dt_date.today(), 'auteur': request.user.pk})
    return render(request, 'Voeux/versement_contrib_add.html', {'form': form, 'contrib': contrib})


@login_required(login_url='/membres/login/')
def delete_versement_contribution(request, pk):
    v = get_object_or_404(VersementContribution, pk=pk)
    contrib_pk = v.contribution_id
    if not (request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )):
        raise PermissionDenied
    if request.method == 'POST':
        v.delete()
        return redirect('contribution_detail', pk=contrib_pk)
    return render(request, 'Voeux/versement_contrib_delete.html', {'versement': v})


# ─── Hiérarchie Contributions ─────────────────────────────────────────────────

def _contrib_stats(qs):
    items = list(qs)
    total_objectif = sum(c.montant_objectif or 0 for c in items)
    total_verse = sum(c.total_verse for c in items)
    return total_objectif, total_verse


@login_required(login_url='/membres/login/')
def contribution_district(request, eglise_pk):
    eglise = get_object_or_404(Eglise, pk=eglise_pk)
    if not _can_manage(request.user, eglise):
        raise PermissionDenied
    type_pk = request.GET.get('type', '')
    contribs = Contribution.objects.filter(eglise=eglise).select_related('membre', 'type_contribution')
    if type_pk:
        contribs = contribs.filter(type_contribution_id=type_pk)
    contribs = contribs.order_by('type_contribution__nom', 'membre__nom')
    total_objectif, total_verse = _contrib_stats(contribs)
    all_types = TypeContribution.objects.filter(actif=True)
    return render(request, 'Voeux/contribution_district.html', {
        'eglise': eglise,
        'contribs': contribs,
        'contrib_count': contribs.count(),
        'total_objectif': total_objectif,
        'total_verse': total_verse,
        'all_types': all_types,
        'selected_type': type_pk,
    })


@login_required(login_url='/membres/login/')
def contribution_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            e = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not e or e.groupe != group:
                raise PermissionDenied
    type_pk = request.GET.get('type', '')
    contribs = _filter_contribs(request.user, Contribution.objects.filter(eglise__groupe=group))
    if type_pk:
        contribs = contribs.filter(type_contribution_id=type_pk)

    eglises = Eglise.objects.filter(groupe=group).order_by('nom')
    eglises_data = []
    for e in eglises:
        cq = contribs.filter(eglise=e).select_related('membre', 'type_contribution').order_by('membre__nom')
        to, tv = _contrib_stats(cq)
        if cq.exists():
            eglises_data.append({
                'eglise': e, 'contribs': cq, 'count': cq.count(),
                'total_objectif': to, 'total_verse': tv,
            })

    to, tv = _contrib_stats(contribs)
    all_types = TypeContribution.objects.filter(actif=True)
    return render(request, 'Voeux/contribution_groupe.html', {
        'groupe': groupe,
        'eglises_data': eglises_data,
        'contrib_count': contribs.count(),
        'total_objectif': to, 'total_verse': tv,
        'all_types': all_types, 'selected_type': type_pk,
    })


@login_required(login_url='/membres/login/')
def contribution_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            e = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not e or e.region != regs:
                raise PermissionDenied
        elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
            e = Eglise.objects.filter(groupe__icontains=p.groupe_assigne).first()
            if not e or e.region != regs:
                raise PermissionDenied
    type_pk = request.GET.get('type', '')
    contribs = _filter_contribs(request.user, Contribution.objects.filter(eglise__region=regs))
    if type_pk:
        contribs = contribs.filter(type_contribution_id=type_pk)

    groupes = Groupe.objects.filter(region=regs).order_by('name')
    groupes_data = []
    for g in groupes:
        cq = contribs.filter(eglise__groupe=g.name)
        to, tv = _contrib_stats(cq)
        if cq.exists():
            groupes_data.append({
                'groupe': g, 'count': cq.count(),
                'total_objectif': to, 'total_verse': tv,
            })

    to, tv = _contrib_stats(contribs)
    all_types = TypeContribution.objects.filter(actif=True)
    return render(request, 'Voeux/contribution_region.html', {
        'region': region,
        'groupes_data': groupes_data,
        'contrib_count': contribs.count(),
        'total_objectif': to, 'total_verse': tv,
        'all_types': all_types, 'selected_type': type_pk,
    })


@login_required(login_url='/membres/login/')
def contribution_national(request):
    if not _is_admin_national(request.user):
        raise PermissionDenied
    type_pk = request.GET.get('type', '')
    contribs = _filter_contribs(request.user, Contribution.objects.all())
    if type_pk:
        contribs = contribs.filter(type_contribution_id=type_pk)

    regions = Region.objects.all().order_by('name')
    regions_data = []
    for r in regions:
        cq = contribs.filter(eglise__region=r.name)
        to, tv = _contrib_stats(cq)
        if cq.exists():
            regions_data.append({
                'region': r, 'count': cq.count(),
                'total_objectif': to, 'total_verse': tv,
            })

    to, tv = _contrib_stats(contribs)
    all_types = TypeContribution.objects.filter(actif=True)
    return render(request, 'Voeux/contribution_national.html', {
        'regions_data': regions_data,
        'contrib_count': contribs.count(),
        'total_objectif': to, 'total_verse': tv,
        'all_types': all_types, 'selected_type': type_pk,
    })


# ════════════════════════════════════════════════════════════════════════════
# MODIFICATION DE MONTANT AVEC JUSTIFICATION
# ════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/membres/login/')
def modifier_montant_voeu(request, pk):
    voeu = get_object_or_404(Voeu.objects.select_related('membre', 'eglise', 'auteur'), pk=pk)
    if not _can_modifier_montant(request.user, voeu.auteur):
        raise PermissionDenied
    if request.method == 'POST':
        form = ModifierMontantVoeuForm(request.POST)
        if form.is_valid():
            ancien = voeu.montant_promis
            nouveau = form.cleaned_data['nouveau_montant']
            justification = form.cleaned_data['justification']
            HistoriqueVoeu.objects.create(
                voeu=voeu,
                ancien_montant=ancien,
                nouveau_montant=nouveau,
                justification=justification,
                auteur=request.user,
            )
            voeu.montant_promis = nouveau
            voeu.save(update_fields=['montant_promis', 'updated'])
            return redirect('voeu_detail', pk=voeu.pk)
    else:
        form = ModifierMontantVoeuForm(initial={'nouveau_montant': voeu.montant_promis})
    return render(request, 'Voeux/modifier_montant_voeu.html', {
        'form': form,
        'voeu': voeu,
    })


@login_required(login_url='/membres/login/')
def corriger_versement_voeu(request, pk):
    versement = get_object_or_404(
        VersementVoeu.objects.select_related('voeu', 'voeu__membre', 'voeu__eglise', 'auteur'), pk=pk)
    if not _can_modifier_montant(request.user, versement.auteur):
        raise PermissionDenied
    if request.method == 'POST':
        form = CorrectionVersementForm(request.POST)
        if form.is_valid():
            ancien = versement.montant
            nouveau = form.cleaned_data['nouveau_montant']
            HistoriqueVersementVoeu.objects.create(
                versement=versement,
                ancien_montant=ancien,
                nouveau_montant=nouveau,
                justification=form.cleaned_data['justification'],
                auteur=request.user,
            )
            versement.montant = nouveau
            versement.save(update_fields=['montant'])
            return redirect('voeu_detail', pk=versement.voeu_id)
    else:
        form = CorrectionVersementForm(initial={'nouveau_montant': versement.montant})
    return render(request, 'Voeux/corriger_versement_voeu.html', {
        'form': form,
        'versement': versement,
    })


@login_required(login_url='/membres/login/')
def corriger_versement_contribution(request, pk):
    versement = get_object_or_404(
        VersementContribution.objects.select_related(
            'contribution', 'contribution__membre', 'contribution__eglise', 'auteur'), pk=pk)
    if not _can_modifier_montant(request.user, versement.auteur):
        raise PermissionDenied
    if request.method == 'POST':
        form = CorrectionVersementForm(request.POST)
        if form.is_valid():
            ancien = versement.montant
            nouveau = form.cleaned_data['nouveau_montant']
            HistoriqueVersementContribution.objects.create(
                versement=versement,
                ancien_montant=ancien,
                nouveau_montant=nouveau,
                justification=form.cleaned_data['justification'],
                auteur=request.user,
            )
            versement.montant = nouveau
            versement.save(update_fields=['montant'])
            return redirect('contribution_detail', pk=versement.contribution_id)
    else:
        form = CorrectionVersementForm(initial={'nouveau_montant': versement.montant})
    return render(request, 'Voeux/corriger_versement_contribution.html', {
        'form': form,
        'versement': versement,
    })


# ════════════════════════════════════════════════════════════════════════════
# TYPES DE CONTRIBUTION (gestion admin)
# ════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/membres/login/')
def type_list(request):
    types = TypeContribution.objects.all()
    peut_gerer = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces in ['ADMIN', 'COMPTABLE']
    )
    return render(request, 'Voeux/type_list.html', {
        'types': types,
        'peut_gerer': peut_gerer,
    })


@login_required(login_url='/membres/login/')
@admin_required
def add_type(request):
    if request.method == 'POST':
        form = TypeContributionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.auteur = request.user
            t.save()
            return redirect('type_list')
    else:
        form = TypeContributionForm()
    return render(request, 'Voeux/type_form.html', {'form': form, 'action': 'Ajouter'})


@login_required(login_url='/membres/login/')
@admin_required
def edit_type(request, pk):
    t = get_object_or_404(TypeContribution, pk=pk)
    if request.method == 'POST':
        form = TypeContributionForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            return redirect('type_list')
    else:
        form = TypeContributionForm(instance=t)
    return render(request, 'Voeux/type_form.html', {'form': form, 'action': 'Modifier', 'type_obj': t})


@login_required(login_url='/membres/login/')
@admin_required
def delete_type(request, pk):
    t = get_object_or_404(TypeContribution, pk=pk)
    if request.method == 'POST':
        t.delete()
        return redirect('type_list')
    return render(request, 'Voeux/type_delete.html', {'type_obj': t})


# ════════════════════════════════════════════════════════════════════════════
# GESTION DES HISTORIQUES (suppression ligne / vider tout)
# ════════════════════════════════════════════════════════════════════════════

def _admin_required_check(user):
    if not _is_admin_national(user):
        raise PermissionDenied


@login_required(login_url='/membres/login/')
def delete_historique_voeu(request, pk):
    h = get_object_or_404(HistoriqueVoeu, pk=pk)
    _admin_required_check(request.user)
    voeu_pk = h.voeu_id
    if request.method == 'POST':
        h.delete()
    return redirect('voeu_detail', pk=voeu_pk)


@login_required(login_url='/membres/login/')
def vider_historiques_voeu(request, voeu_pk):
    voeu = get_object_or_404(Voeu, pk=voeu_pk)
    _admin_required_check(request.user)
    if request.method == 'POST':
        voeu.historiques.all().delete()
    return redirect('voeu_detail', pk=voeu_pk)


@login_required(login_url='/membres/login/')
def delete_historique_contribution(request, pk):
    h = get_object_or_404(HistoriqueContribution, pk=pk)
    _admin_required_check(request.user)
    contrib_pk = h.contribution_id
    if request.method == 'POST':
        h.delete()
    return redirect('contribution_detail', pk=contrib_pk)


@login_required(login_url='/membres/login/')
def vider_historiques_contribution(request, contrib_pk):
    contrib = get_object_or_404(Contribution, pk=contrib_pk)
    _admin_required_check(request.user)
    if request.method == 'POST':
        contrib.historiques.all().delete()
    return redirect('contribution_detail', pk=contrib_pk)


@login_required(login_url='/membres/login/')
def delete_historique_versement_voeu(request, pk):
    h = get_object_or_404(HistoriqueVersementVoeu, pk=pk)
    _admin_required_check(request.user)
    voeu_pk = h.versement.voeu_id
    if request.method == 'POST':
        h.delete()
    return redirect('voeu_detail', pk=voeu_pk)


@login_required(login_url='/membres/login/')
def vider_corrections_versements_voeu(request, voeu_pk):
    voeu = get_object_or_404(Voeu, pk=voeu_pk)
    _admin_required_check(request.user)
    if request.method == 'POST':
        HistoriqueVersementVoeu.objects.filter(versement__voeu=voeu).delete()
    return redirect('voeu_detail', pk=voeu_pk)


@login_required(login_url='/membres/login/')
def delete_historique_versement_contribution(request, pk):
    h = get_object_or_404(HistoriqueVersementContribution, pk=pk)
    _admin_required_check(request.user)
    contrib_pk = h.versement.contribution_id
    if request.method == 'POST':
        h.delete()
    return redirect('contribution_detail', pk=contrib_pk)


@login_required(login_url='/membres/login/')
def vider_corrections_versements_contribution(request, contrib_pk):
    contrib = get_object_or_404(Contribution, pk=contrib_pk)
    _admin_required_check(request.user)
    if request.method == 'POST':
        HistoriqueVersementContribution.objects.filter(versement__contribution=contrib).delete()
    return redirect('contribution_detail', pk=contrib_pk)


# ════════════════════════════════════════════════════════════════════════════
# PAGE HISTORIQUE GLOBAL
# ════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/membres/login/')
def historique_global(request):
    is_admin = _is_admin_national(request.user)

    # Actions de vidage global (POST)
    if request.method == 'POST' and is_admin:
        action = request.POST.get('action', '')
        section_redirect = 'voeux'
        if action == 'vider_global_voeux':
            HistoriqueVoeu.objects.all().delete()
            section_redirect = 'voeux'
        elif action == 'vider_global_contributions':
            HistoriqueContribution.objects.all().delete()
            section_redirect = 'contributions'
        elif action == 'vider_global_versements_voeux':
            HistoriqueVersementVoeu.objects.all().delete()
            section_redirect = 'versements_voeux'
        elif action == 'vider_global_versements_contributions':
            HistoriqueVersementContribution.objects.all().delete()
            section_redirect = 'versements_contributions'
        return redirect(f"{request.path}?section={section_redirect}")

    # Filtres communs
    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    section = request.GET.get('section', 'voeux')  # onglet actif

    def _apply_dates(qs):
        if date_debut:
            qs = qs.filter(created__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(created__date__lte=date_fin)
        return qs

    if not is_admin:
        raise PermissionDenied

    # ── Historiques modifications montant promis (Voeux) ──
    hv = HistoriqueVoeu.objects.select_related(
        'voeu', 'voeu__membre', 'voeu__eglise', 'auteur').order_by('-created')
    if region:
        hv = hv.filter(voeu__eglise__region__icontains=region)
    if groupe:
        hv = hv.filter(voeu__eglise__groupe__icontains=groupe)
    hv = _apply_dates(hv)

    # ── Historiques modifications montant objectif (Contributions) ──
    hc = HistoriqueContribution.objects.select_related(
        'contribution', 'contribution__membre', 'contribution__eglise', 'auteur').order_by('-created')
    if region:
        hc = hc.filter(contribution__eglise__region__icontains=region)
    if groupe:
        hc = hc.filter(contribution__eglise__groupe__icontains=groupe)
    hc = _apply_dates(hc)

    # ── Corrections versements Voeux ──
    hvv = HistoriqueVersementVoeu.objects.select_related(
        'versement', 'versement__voeu', 'versement__voeu__membre',
        'versement__voeu__eglise', 'auteur').order_by('-created')
    if region:
        hvv = hvv.filter(versement__voeu__eglise__region__icontains=region)
    if groupe:
        hvv = hvv.filter(versement__voeu__eglise__groupe__icontains=groupe)
    hvv = _apply_dates(hvv)

    # ── Corrections versements Contributions ──
    hvc = HistoriqueVersementContribution.objects.select_related(
        'versement', 'versement__contribution', 'versement__contribution__membre',
        'versement__contribution__eglise', 'auteur').order_by('-created')
    if region:
        hvc = hvc.filter(versement__contribution__eglise__region__icontains=region)
    if groupe:
        hvc = hvc.filter(versement__contribution__eglise__groupe__icontains=groupe)
    hvc = _apply_dates(hvc)

    all_regions = Region.objects.all().order_by('name')
    all_groupes = Groupe.objects.all().order_by('name')

    return render(request, 'Voeux/historique_global.html', {
        'hv': hv,
        'hc': hc,
        'hvv': hvv,
        'hvc': hvc,
        'section': section,
        'is_admin': is_admin,
        'all_regions': all_regions,
        'all_groupes': all_groupes,
        'selected_region': region,
        'selected_groupe': groupe,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'total_hv': hv.count(),
        'total_hc': hc.count(),
        'total_hvv': hvv.count(),
        'total_hvc': hvc.count(),
    })
