from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import QuotaRegion, QuotaGroupe, QuotaEglise, VersementQuota, PromesseQuota, GRAND_LOME
from .forms import QuotaRegionForm, QuotaGroupeForm, QuotaEgliseForm, VersementQuotaForm, PromesseQuotaForm
from Eglises.models import Eglise, Region as RegionModel, Groupe as GroupeModel
from datetime import date


def _annee(request):
    return int(request.GET.get('annee', date.today().year))


def _verse_region(region_name):
    return int(VersementQuota.objects.filter(eglise__region=region_name).aggregate(s=Sum('montant'))['s'] or 0)


def _verse_groupe(groupe_name, region_name=None):
    qs = VersementQuota.objects.filter(eglise__groupe=groupe_name)
    if region_name:
        qs = qs.filter(eglise__region=region_name)
    return int(qs.aggregate(s=Sum('montant'))['s'] or 0)


def _verse_eglise(eglise):
    return int(VersementQuota.objects.filter(eglise=eglise).aggregate(s=Sum('montant'))['s'] or 0)


def _pct(verse, quota):
    return min(round(verse * 100 / quota), 100) if quota else 0


# ─── Vue nationale ────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_national(request):
    annee = _annee(request)
    regions = RegionModel.objects.all().order_by('name')
    rows = []
    total_quota = total_verse = 0

    for i, region in enumerate(regions, 1):
        if region.name == GRAND_LOME:
            # Grand Lomé : quota = somme des QuotaGroupe de cette région
            rq = int(QuotaGroupe.objects.filter(region=region.name, annee=annee).aggregate(s=Sum('montant'))['s'] or 0)
        else:
            obj = QuotaRegion.objects.filter(region=region.name, annee=annee).first()
            rq = int(obj.montant) if obj else 0

        rv = _verse_region(region.name)
        reste = rq - rv
        rows.append({'num': i, 'nom': region.name, 'quota': rq, 'verse': rv, 'reste': reste, 'pct': _pct(rv, rq)})
        total_quota += rq
        total_verse += rv

    context = {
        'rows': rows,
        'total_quota': total_quota,
        'total_verse': total_verse,
        'total_reste': total_quota - total_verse,
        'total_pct': _pct(total_verse, total_quota),
        'annee': annee,
        'grand_lome': GRAND_LOME,
    }
    return render(request, 'Quotas/quota_national.html', context)


# ─── Vue par région (groupes) ─────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_region(request, region):
    annee = _annee(request)
    groupes_qs = GroupeModel.objects.filter(region=region).order_by('name')
    rows = []
    total_quota = total_verse = 0

    # Quota attribué à la région entière
    if region == GRAND_LOME:
        quota_region_total = int(QuotaGroupe.objects.filter(region=region, annee=annee).aggregate(s=Sum('montant'))['s'] or 0)
    else:
        obj = QuotaRegion.objects.filter(region=region, annee=annee).first()
        quota_region_total = int(obj.montant) if obj else 0

    # Somme déjà distribuée aux groupes
    distribue = int(QuotaGroupe.objects.filter(region=region, annee=annee).aggregate(s=Sum('montant'))['s'] or 0)
    restant_a_distribuer = quota_region_total - distribue if region != GRAND_LOME else 0

    for i, groupe in enumerate(groupes_qs, 1):
        obj = QuotaGroupe.objects.filter(groupe=groupe.name, annee=annee).first()
        gq = int(obj.montant) if obj else 0
        gv = _verse_groupe(groupe.name, region)
        reste = gq - gv
        rows.append({'num': i, 'nom': groupe.name, 'quota': gq, 'verse': gv, 'reste': reste, 'pct': _pct(gv, gq)})
        total_quota += gq
        total_verse += gv

    context = {
        'rows': rows,
        'total_quota': total_quota,
        'total_verse': total_verse,
        'total_reste': total_quota - total_verse,
        'total_pct': _pct(total_verse, total_quota),
        'quota_region_total': quota_region_total,
        'restant_a_distribuer': restant_a_distribuer,
        'annee': annee,
        'region': region,
        'is_grand_lome': region == GRAND_LOME,
    }
    return render(request, 'Quotas/quota_region.html', context)


# ─── Vue par groupe (églises) ─────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_groupe(request, groupe):
    annee = _annee(request)
    eglises = Eglise.objects.filter(groupe=groupe).order_by('nom')

    # Quota attribué au groupe
    obj = QuotaGroupe.objects.filter(groupe=groupe, annee=annee).first()
    quota_groupe_total = int(obj.montant) if obj else 0
    region = obj.region if obj else (eglises.first().region if eglises.exists() else '')

    distribue = int(QuotaEglise.objects.filter(eglise__groupe=groupe, annee=annee).aggregate(s=Sum('montant'))['s'] or 0)
    restant_a_distribuer = quota_groupe_total - distribue

    rows = []
    total_quota = total_verse = 0
    for i, eglise in enumerate(eglises, 1):
        eq_obj = QuotaEglise.objects.filter(eglise=eglise, annee=annee).first()
        eq = int(eq_obj.montant) if eq_obj else 0
        ev = _verse_eglise(eglise)
        reste = eq - ev
        rows.append({'num': i, 'eglise': eglise, 'quota': eq, 'verse': ev, 'reste': reste, 'pct': _pct(ev, eq), 'quota_pk': eq_obj.pk if eq_obj else None})
        total_quota += eq
        total_verse += ev

    context = {
        'rows': rows,
        'total_quota': total_quota,
        'total_verse': total_verse,
        'total_reste': total_quota - total_verse,
        'total_pct': _pct(total_verse, total_quota),
        'quota_groupe_total': quota_groupe_total,
        'restant_a_distribuer': restant_a_distribuer,
        'annee': annee,
        'groupe': groupe,
        'region': region,
    }
    return render(request, 'Quotas/quota_groupe.html', context)


# ─── Attributions ─────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_attribuer_region(request):
    regions = RegionModel.objects.exclude(name=GRAND_LOME).order_by('name')
    if request.method == 'POST':
        form = QuotaRegionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.auteur = request.user
            # update or create
            QuotaRegion.objects.update_or_create(
                region=q.region, annee=q.annee,
                defaults={'montant': q.montant, 'auteur': q.auteur}
            )
            return redirect('quota_national')
    else:
        form = QuotaRegionForm()
    return render(request, 'Quotas/quota_attribuer_region.html', {
        'form': form, 'regions': regions,
        'titre': 'Attribuer un quota à une région',
    })


@login_required(login_url='/membres/login/')
def quota_attribuer_groupe(request, region=None):
    regions = RegionModel.objects.all().order_by('name')
    groupes = GroupeModel.objects.all().order_by('name')
    region_sel = region or request.GET.get('region', '')
    if region_sel:
        groupes = groupes.filter(region=region_sel)

    if request.method == 'POST':
        form = QuotaGroupeForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.auteur = request.user
            QuotaGroupe.objects.update_or_create(
                groupe=q.groupe, annee=q.annee,
                defaults={'montant': q.montant, 'region': q.region, 'auteur': q.auteur}
            )
            return redirect('quota_region', region=q.region)
    else:
        initial = {'region': region_sel} if region_sel else {}
        form = QuotaGroupeForm(initial=initial)

    return render(request, 'Quotas/quota_attribuer_groupe.html', {
        'form': form, 'regions': regions, 'groupes': groupes,
        'region_sel': region_sel,
        'titre': 'Attribuer un quota à un groupe',
    })


@login_required(login_url='/membres/login/')
def quota_attribuer_eglise(request, groupe=None):
    groupe_sel = groupe or request.GET.get('groupe', '')
    eglises = Eglise.objects.all().order_by('groupe', 'nom')
    if groupe_sel:
        eglises = eglises.filter(groupe=groupe_sel)

    if request.method == 'POST':
        form = QuotaEgliseForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.auteur = request.user
            quota_obj, _ = QuotaEglise.objects.update_or_create(
                eglise=q.eglise, annee=q.annee,
                defaults={'montant': q.montant, 'auteur': q.auteur}
            )
            return redirect('quota_eglise_detail', pk=quota_obj.pk)
    else:
        form = QuotaEgliseForm()
        if groupe_sel:
            form.fields['eglise'].queryset = Eglise.objects.filter(groupe=groupe_sel)

    return render(request, 'Quotas/quota_attribuer_eglise.html', {
        'form': form, 'groupe_sel': groupe_sel,
        'titre': 'Attribuer un quota à une église',
    })


# ─── Versements quota ─────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def versement_quota_add(request):
    eglise_pk = request.GET.get('eglise')
    initial = {}
    if eglise_pk:
        initial['eglise'] = eglise_pk
    if request.method == 'POST':
        form = VersementQuotaForm(request.POST, request.FILES)
        if form.is_valid():
            v = form.save(commit=False)
            v.auteur = request.user
            v.save()
            return redirect('versement_quota_list')
    else:
        form = VersementQuotaForm(initial=initial)
    return render(request, 'Quotas/versement_quota_form.html', {
        'form': form, 'titre': 'Enregistrer un paiement quota'
    })


@login_required(login_url='/membres/login/')
def versement_quota_list(request):
    qs = VersementQuota.objects.select_related('eglise', 'auteur').order_by('-date')
    user = request.user
    if not user.is_superuser and hasattr(user, 'profile'):
        p = user.profile
        if p.niveau_acces == 'REGION' and p.region_assignee:
            qs = qs.filter(eglise__region=p.region_assignee)
        elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
            qs = qs.filter(eglise__groupe=p.groupe_assigne)
        elif p.niveau_acces == 'DISTRICT' and p.district_assigne:
            qs = qs.filter(eglise__nom=p.district_assigne)
    total = int(qs.aggregate(s=Sum('montant'))['s'] or 0)
    return render(request, 'Quotas/versement_quota_list.html', {'versements': qs, 'total': total})


@login_required(login_url='/membres/login/')
def versement_quota_supprimer(request, pk):
    versement = get_object_or_404(VersementQuota, pk=pk)
    if request.method == 'POST':
        versement.delete()
        return redirect('versement_quota_list')
    return render(request, 'Quotas/versement_quota_confirm_delete.html', {'object': versement})


# ─── Détail quota d'une église + promesses ────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_eglise_detail(request, pk):
    quota = get_object_or_404(QuotaEglise, pk=pk)
    eglise = quota.eglise

    promesses_qs = quota.promesses.all()
    paginator = Paginator(promesses_qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    total_promis = int(promesses_qs.aggregate(s=Sum('montant_promis'))['s'] or 0)
    total_paye = int(promesses_qs.aggregate(s=Sum('montant_paye'))['s'] or 0)
    quota_montant = int(quota.montant)
    # Reste = ce que les membres doivent encore payer
    reste = quota_montant - total_paye
    # Surplus = si le total payé dépasse le quota
    surplus_paye = total_paye - quota_montant  # positif = surplus, négatif = reste
    pct_promis = min(round(total_promis * 100 / quota_montant), 999) if quota_montant else 0
    pct_paye = min(round(total_paye * 100 / quota_montant), 999) if quota_montant else 0

    context = {
        'quota': quota,
        'eglise': eglise,
        'page_obj': page,
        'total_promis': total_promis,
        'total_paye': total_paye,
        'quota_montant': quota_montant,
        'reste': reste,
        'surplus_paye': surplus_paye,
        'pct_promis': pct_promis,
        'pct_paye': pct_paye,
    }
    return render(request, 'Quotas/quota_eglise_detail.html', context)


@login_required(login_url='/membres/login/')
def promesse_add(request, quota_pk):
    quota = get_object_or_404(QuotaEglise, pk=quota_pk)
    eglise = quota.eglise
    if request.method == 'POST':
        form = PromesseQuotaForm(request.POST, eglise=eglise)
        if form.is_valid():
            p = form.save(commit=False)
            p.quota_eglise = quota
            p.save()
            return redirect('quota_eglise_detail', pk=quota_pk)
    else:
        form = PromesseQuotaForm(eglise=eglise)
    return render(request, 'Quotas/promesse_form.html', {
        'form': form, 'quota': quota, 'titre': 'Ajouter une promesse',
    })


@login_required(login_url='/membres/login/')
def promesse_edit(request, pk):
    promesse = get_object_or_404(PromesseQuota, pk=pk)
    quota = promesse.quota_eglise
    eglise = quota.eglise
    if request.method == 'POST':
        form = PromesseQuotaForm(request.POST, instance=promesse, eglise=eglise)
        if form.is_valid():
            form.save()
            return redirect('quota_eglise_detail', pk=quota.pk)
    else:
        form = PromesseQuotaForm(instance=promesse, eglise=eglise)
    return render(request, 'Quotas/promesse_form.html', {
        'form': form, 'quota': quota, 'titre': 'Modifier la promesse',
    })


@login_required(login_url='/membres/login/')
def promesse_delete(request, pk):
    promesse = get_object_or_404(PromesseQuota, pk=pk)
    quota_pk = promesse.quota_eglise.pk
    if request.method == 'POST':
        promesse.delete()
        return redirect('quota_eglise_detail', pk=quota_pk)
    return render(request, 'Quotas/promesse_confirm_delete.html', {'object': promesse})


# ─── Liste de toutes les quotas d'église ─────────────────────────────────────

@login_required(login_url='/membres/login/')
def quota_eglise_list(request):
    annee = _annee(request)
    quotas = QuotaEglise.objects.filter(annee=annee).select_related('eglise').order_by('eglise__groupe', 'eglise__nom')
    context = {'quotas': quotas, 'annee': annee}
    return render(request, 'Quotas/quota_eglise_list.html', context)
