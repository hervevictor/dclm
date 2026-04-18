from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from .models import NouveauVenu
from .forms import NouveauVenuForm, FiltreNouveauVenuForm
from Eglises.models import Eglise, Groupe as GroupeModel, Region as RegionModel
from datetime import date
import json


# ─── Filtrage commun ──────────────────────────────────────────────────────────

def _apply_filters(qs, form):
    if not form.is_valid():
        return qs
    d = form.cleaned_data
    mode = d.get('mode')
    if mode == 'mois' and d.get('mois'):
        m = d['mois']
        qs = qs.filter(date_venue__year=m.year, date_venue__month=m.month)
    elif mode == 'annee' and d.get('annee'):
        qs = qs.filter(date_venue__year=d['annee'])
    elif mode == 'periode' and d.get('date_debut') and d.get('date_fin'):
        qs = qs.filter(date_venue__range=[d['date_debut'], d['date_fin']])
    if d.get('origine'):
        qs = qs.filter(origine=d['origine'])
    if d.get('statut'):
        qs = qs.filter(statut=d['statut'])
    if d.get('categorie'):
        qs = qs.filter(categorie=d['categorie'])
    return qs


def _chart_data(qs):
    """Retourne les données mensuelles pour Chart.js (12 derniers mois)."""
    from django.db.models.functions import TruncMonth
    data = (
        qs.annotate(mois=TruncMonth('date_venue'))
          .values('mois')
          .annotate(total=Count('id'))
          .order_by('mois')
    )
    labels = [str(r['mois'])[:7] for r in data]
    values = [r['total'] for r in data]
    return labels, values


def _stats(qs):
    total = qs.count()
    restes = qs.filter(statut='RESTE').count()
    partis = qs.filter(statut='PARTI').count()
    suivis = qs.filter(statut='SUIVI').count()
    hommes = qs.filter(sexe='H').count()
    femmes = qs.filter(sexe='F').count()
    jeunes = qs.filter(categorie='JEUNE').count()
    enfants = qs.filter(categorie='ENFANT').count()
    return {
        'total': total, 'restes': restes, 'partis': partis, 'suivis': suivis,
        'hommes': hommes, 'femmes': femmes, 'jeunes': jeunes, 'enfants': enfants,
        'taux_retention': round(restes * 100 / total) if total else 0,
    }


# ─── Dashboard national ───────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def croissance_national(request):
    form = FiltreNouveauVenuForm(request.GET or None)
    qs = _apply_filters(NouveauVenu.objects.select_related('eglise'), form)

    regions = RegionModel.objects.all().order_by('name')
    rows = []
    for region in regions:
        rqs = qs.filter(eglise__region=region.name)
        total = rqs.count()
        restes = rqs.filter(statut='RESTE').count()
        rows.append({
            'nom': region.name,
            'total': total,
            'restes': restes,
            'partis': rqs.filter(statut='PARTI').count(),
            'taux': round(restes * 100 / total) if total else 0,
        })

    labels, values = _chart_data(qs)
    context = {
        'form': form,
        'rows': rows,
        'stats': _stats(qs),
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
        'niveau': 'National',
    }
    return render(request, 'Croissance/croissance_national.html', context)


# ─── Dashboard par région ─────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def croissance_region(request, region):
    form = FiltreNouveauVenuForm(request.GET or None)
    qs = _apply_filters(
        NouveauVenu.objects.filter(eglise__region=region).select_related('eglise'), form
    )

    groupes = GroupeModel.objects.filter(region=region).order_by('name')
    rows = []
    for groupe in groupes:
        gqs = qs.filter(eglise__groupe=groupe.name)
        total = gqs.count()
        restes = gqs.filter(statut='RESTE').count()
        rows.append({
            'nom': groupe.name,
            'total': total,
            'restes': restes,
            'partis': gqs.filter(statut='PARTI').count(),
            'taux': round(restes * 100 / total) if total else 0,
        })

    labels, values = _chart_data(qs)
    context = {
        'form': form,
        'rows': rows,
        'stats': _stats(qs),
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
        'niveau': region,
        'region': region,
    }
    return render(request, 'Croissance/croissance_region.html', context)


# ─── Dashboard par groupe ─────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def croissance_groupe(request, groupe):
    form = FiltreNouveauVenuForm(request.GET or None)
    qs = _apply_filters(
        NouveauVenu.objects.filter(eglise__groupe=groupe).select_related('eglise'), form
    )

    eglises = Eglise.objects.filter(groupe=groupe).order_by('nom')
    rows = []
    for eglise in eglises:
        eqs = qs.filter(eglise=eglise)
        total = eqs.count()
        restes = eqs.filter(statut='RESTE').count()
        rows.append({
            'nom': eglise.nom,
            'eglise': eglise,
            'total': total,
            'restes': restes,
            'partis': eqs.filter(statut='PARTI').count(),
            'taux': round(restes * 100 / total) if total else 0,
        })

    labels, values = _chart_data(qs)
    context = {
        'form': form,
        'rows': rows,
        'stats': _stats(qs),
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
        'niveau': groupe,
        'groupe': groupe,
    }
    return render(request, 'Croissance/croissance_groupe.html', context)


# ─── Dashboard par église ─────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def croissance_eglise(request, pk):
    eglise = get_object_or_404(Eglise, pk=pk)
    form = FiltreNouveauVenuForm(request.GET or None)
    qs = _apply_filters(
        NouveauVenu.objects.filter(eglise=eglise), form
    )

    labels, values = _chart_data(qs)
    context = {
        'form': form,
        'eglise': eglise,
        'nouveaux': qs,
        'stats': _stats(qs),
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
        'niveau': eglise.nom,
    }
    return render(request, 'Croissance/croissance_eglise.html', context)


# ─── CRUD nouveaux venus ──────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def nouveau_venu_liste(request):
    form = FiltreNouveauVenuForm(request.GET or None)
    qs = _apply_filters(NouveauVenu.objects.select_related('eglise'), form)

    user = request.user
    if not user.is_superuser and hasattr(user, 'profile'):
        p = user.profile
        if p.niveau_acces == 'REGION' and p.region_assignee:
            qs = qs.filter(eglise__region=p.region_assignee)
        elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
            qs = qs.filter(eglise__groupe=p.groupe_assigne)
        elif p.niveau_acces == 'DISTRICT' and p.district_assigne:
            qs = qs.filter(eglise__nom=p.district_assigne)

    context = {
        'form': form,
        'nouveaux': qs,
        'total': qs.count(),
    }
    return render(request, 'Croissance/nouveau_venu_liste.html', context)


@login_required(login_url='/membres/login/')
def nouveau_venu_add(request):
    eglise_pk = request.GET.get('eglise')
    initial = {'eglise': eglise_pk} if eglise_pk else {}
    if request.method == 'POST':
        form = NouveauVenuForm(request.POST)
        if form.is_valid():
            nv = form.save(commit=False)
            nv.auteur = request.user
            nv.save()
            return redirect('nouveau_venu_liste')
    else:
        form = NouveauVenuForm(initial=initial)
    return render(request, 'Croissance/nouveau_venu_form.html', {'form': form, 'titre': 'Enregistrer un nouveau venu'})


@login_required(login_url='/membres/login/')
def nouveau_venu_edit(request, pk):
    nv = get_object_or_404(NouveauVenu, pk=pk)
    if request.method == 'POST':
        form = NouveauVenuForm(request.POST, instance=nv)
        if form.is_valid():
            form.save()
            return redirect('nouveau_venu_liste')
    else:
        form = NouveauVenuForm(instance=nv)
    return render(request, 'Croissance/nouveau_venu_form.html', {'form': form, 'titre': 'Modifier', 'obj': nv})


@login_required(login_url='/membres/login/')
def nouveau_venu_delete(request, pk):
    nv = get_object_or_404(NouveauVenu, pk=pk)
    if request.method == 'POST':
        nv.delete()
        return redirect('nouveau_venu_liste')
    return render(request, 'Croissance/nouveau_venu_confirm_delete.html', {'object': nv})
