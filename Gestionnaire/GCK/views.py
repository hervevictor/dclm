from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .models import BilanGCK, BilanConferenceMinistres, BilanImpact
from .forms import BilanGCKForm
from .resources import BilanGCKResource
from Eglises.models import Eglise, Groupe, Region
from Eglises.templatetags.region_labels import is_grand_lome, get_labels
from Membres.utils import filter_by_rbac, RBACMixin, AdminOnlyMixin
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tablib import Dataset

MOIS_FR = [
    ('', '— Tous —'),
    ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'), ('4', 'Avril'),
    ('5', 'Mai'), ('6', 'Juin'), ('7', 'Juillet'), ('8', 'Août'),
    ('9', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre'),
]


# ─── Filtres communs ───────────────────────────────────────────────────────────

def _apply_date_filters(bilans, params):
    start_date = params.get('start_date', '')
    end_date = params.get('end_date', '')
    mois = params.get('mois', '')
    jour = params.get('jour', '')
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])
    elif start_date:
        bilans = bilans.filter(date__gte=start_date)
    elif end_date:
        bilans = bilans.filter(date__lte=end_date)
    if mois:
        bilans = bilans.filter(date__month=int(mois))
    if jour:
        bilans = bilans.filter(date__day=int(jour))
    return bilans, start_date, end_date, mois, jour


# ─── Ajouter un bilan ──────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_gck(request):
    user = request.user
    avertissement = None

    district_unique = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        district_unique = user.profile.district_assigne

    if request.method == 'POST':
        form = BilanGCKForm(request.POST, user=user)
        if form.is_valid():
            eglise_choisie = form.cleaned_data['eglise']
            if district_unique and district_unique.lower() not in eglise_choisie.nom.lower():
                avertissement = f"Attention : vous avez soumis un rapport pour « {eglise_choisie.nom} » alors que votre district assigné est « {district_unique} »."
            bilan = form.save()
            return redirect('gck_detail', pk=bilan.pk)
    else:
        form = BilanGCKForm(user=user)

    return render(request, 'GCK/add_gck.html', {
        'form': form,
        'avertissement': avertissement,
        'district_unique': district_unique,
    })


# ─── Liste (filtrée par RBAC) ──────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_list(request):
    bilans = BilanGCK.objects.all()
    bilans = filter_by_rbac(request.user, bilans, 'bilan')

    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    district = request.GET.get('district', '')
    avec_convertis = request.GET.get('convertis', '')

    if region:
        bilans = bilans.filter(eglise__region__icontains=region)
    if groupe:
        bilans = bilans.filter(eglise__groupe__icontains=groupe)
    if district:
        bilans = bilans.filter(eglise__nom__icontains=district)
    if avec_convertis == '1':
        bilans = bilans.filter(nouveaux_convertis__gt=0)

    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)
    bilans = bilans.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')
    totaux = _compute_totaux(bilans)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        label = _export_label(region, groupe, district, start_date, end_date, mois, jour, avec_convertis)
        return _export_gck(bilans, totaux, fmt, label)

    all_eglises = filter_by_rbac(request.user, Eglise.objects.all(), 'eglise').order_by('nom')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')
    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')

    context = {
        'bilans': bilans,
        'bilan_count': bilans.count(),
        'start_date': start_date,
        'end_date': end_date,
        'mois': mois,
        'jour': jour,
        'mois_fr': MOIS_FR,
        'all_eglises': all_eglises,
        'all_groupes': all_groupes,
        'all_regions': all_regions,
        'selected_region': region,
        'selected_groupe': groupe,
        'selected_district': district,
        'avec_convertis': avec_convertis,
        **totaux,
    }
    return render(request, 'GCK/gck_list.html', context)


# ─── Détail ────────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_detail(request, pk):
    bilan = get_object_or_404(BilanGCK, pk=pk)
    from Eglises.views import can_edit_eglise
    # Contrôle d'accès en lecture : même règle que pour la gestion
    if not can_edit_eglise(request.user, bilan.eglise):
        raise PermissionDenied
    peut_modifier = can_edit_eglise(request.user, bilan.eglise)
    peut_supprimer = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN'
    )
    return render(request, 'GCK/gck_detail.html', {
        'bilan': bilan,
        'peut_modifier': peut_modifier,
        'peut_supprimer': peut_supprimer,
    })


# ─── Modifier ──────────────────────────────────────────────────────────────────

class EditGCK(RBACMixin, UpdateView):
    model = BilanGCK
    form_class = BilanGCKForm
    template_name = 'GCK/edit_gck.html'

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


# ─── Supprimer ─────────────────────────────────────────────────────────────────

class DeleteGCK(AdminOnlyMixin, DeleteView):
    model = BilanGCK
    template_name = 'GCK/delete_gck.html'
    success_url = reverse_lazy('gck_list')


# ─── Rapport par District ──────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_district(request, dist_pk):
    eglise = get_object_or_404(Eglise, pk=dist_pk)
    from Eglises.views import can_edit_eglise
    if not can_edit_eglise(request.user, eglise):
        raise PermissionDenied
    bilans = BilanGCK.objects.filter(eglise=eglise)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        totaux = _compute_totaux(bilans)
        label = f"{eglise.nom} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export_gck(bilans, totaux, fmt, label)

    bilans = bilans.order_by('-date')
    totaux = _compute_totaux(bilans)

    context = {
        'eglise': eglise, 'bilans': bilans, 'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date, 'mois': mois, 'jour': jour,
        'mois_fr': MOIS_FR, **totaux,
    }
    return render(request, 'GCK/gck_district.html', context)


# ─── Rapport par Groupe ────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    # DISTRICT ne peut pas voir la page groupe (sauf si c'est son groupe)
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            eglise_district = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not eglise_district or eglise_district.groupe != group:
                raise PermissionDenied
    bilans = BilanGCK.objects.filter(eglise__groupe=group)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        totaux = _compute_totaux(bilans)
        label = f"{groupe.name} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export_gck(bilans, totaux, fmt, label)

    eglises = Eglise.objects.filter(groupe=group)
    districts_data = []
    for eglise in eglises:
        b = bilans.filter(eglise=eglise)
        if b.exists():
            t = _compute_totaux(b)
            districts_data.append({'eglise': eglise, 'count': b.count(), **t})

    totaux = _compute_totaux(bilans)
    context = {
        'groupe': groupe, 'districts_data': districts_data,
        'bilan_count': bilans.count(), 'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR, **totaux,
    }
    return render(request, 'GCK/gck_groupe.html', context)


# ─── Rapport par Région ────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    # DISTRICT et GROUPE ne peuvent pas voir une région hors de leur périmètre
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        if p.niveau_acces == 'DISTRICT' and p.district_assigne:
            eglise_district = Eglise.objects.filter(nom__icontains=p.district_assigne).first()
            if not eglise_district or eglise_district.region != regs:
                raise PermissionDenied
        elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
            eglise_groupe = Eglise.objects.filter(groupe__icontains=p.groupe_assigne).first()
            if not eglise_groupe or eglise_groupe.region != regs:
                raise PermissionDenied
    bilans = BilanGCK.objects.filter(eglise__region=regs)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        totaux = _compute_totaux(bilans)
        label = f"Région {region.name} — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export_gck(bilans, totaux, fmt, label)

    groupes = Groupe.objects.filter(region=regs)
    groupes_data = []
    for g in groupes:
        b = bilans.filter(eglise__groupe=g.name)
        if b.exists():
            t = _compute_totaux(b)
            groupes_data.append({'groupe': g, 'count': b.count(), **t})

    totaux = _compute_totaux(bilans)
    context = {
        'region': region, 'groupes_data': groupes_data,
        'bilan_count': bilans.count(), 'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR, **totaux,
    }
    return render(request, 'GCK/gck_region.html', context)


# ─── Rapport National ──────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_national(request):
    user = request.user
    if not (user.is_superuser or (
            hasattr(user, 'profile') and user.profile.niveau_acces in ['ADMIN', 'COMPTABLE'])):
        raise PermissionDenied

    bilans = BilanGCK.objects.all()
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        totaux = _compute_totaux(bilans)
        label = f"TOGO — National — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export_gck(bilans, totaux, fmt, label)

    regions = Region.objects.all()
    regions_data = []
    for region in regions:
        b = bilans.filter(eglise__region=region.name)
        if b.exists():
            t = _compute_totaux(b)
            regions_data.append({'region': region, 'count': b.count(), **t})

    totaux = _compute_totaux(bilans)
    context = {
        'regions_data': regions_data,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    }
    return render(request, 'GCK/gck_national.html', context)


# ─── Récapitulatif par date ────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_recapitulatif(request):
    user = request.user
    if not (user.is_superuser or (
            hasattr(user, 'profile') and user.profile.niveau_acces in ['ADMIN', 'COMPTABLE'])):
        raise PermissionDenied

    bilans = BilanGCK.objects.all()
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    # Grouper par date
    dates = bilans.values_list('date', flat=True).distinct().order_by('date')
    dates_data = []
    for d in dates:
        b = bilans.filter(date=d)
        t = _compute_totaux(b)
        dates_data.append({'date': d, 'count': b.count(), **t})

    totaux = _compute_totaux(bilans)

    # Calcul des moyennes (si plusieurs dates)
    nb_dates = len(dates_data)
    moyennes = {}
    if nb_dates > 0:
        moyennes = {
            'adultes_h': round(totaux['total_adultes_h'] / nb_dates),
            'adultes_f': round(totaux['total_adultes_f'] / nb_dates),
            'adultes': round(totaux['total_adultes'] / nb_dates),
            'jeunes_h': round(totaux['total_jeunes_h'] / nb_dates),
            'jeunes_f': round(totaux['total_jeunes_f'] / nb_dates),
            'jeunes': round(totaux['total_jeunes'] / nb_dates),
            'enfants': round(totaux['total_enfants'] / nb_dates),
            'total': round(totaux['total_participants'] / nb_dates),
            'convertis': round(totaux['total_convertis'] / nb_dates),
        }

    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        label = f"Récapitulatif national — {_export_label('', '', '', start_date, end_date, mois, jour, '')}"
        return _export_recapitulatif(dates_data, totaux, moyennes, fmt, label)

    context = {
        'dates_data': dates_data,
        'nb_dates': nb_dates,
        'moyennes': moyennes,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
        **totaux,
    }
    return render(request, 'GCK/gck_recapitulatif.html', context)


# ─── Convertis : page principale ──────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_convertis(request):
    bilans = BilanGCK.objects.filter(nouveaux_convertis__gt=0)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    all_regions = Region.objects.all().order_by('name')

    # Grand Lomé : afficher directement les groupes
    grand_lome_data = []
    # Autres régions : afficher par région
    regions_data = []

    for region in all_regions:
        b = bilans.filter(eglise__region=region.name)
        total_c = b.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0
        if total_c == 0:
            continue

        if is_grand_lome(region.name):
            groupes = Groupe.objects.filter(region=region.name).order_by('name')
            for g in groupes:
                bg = b.filter(eglise__groupe=g.name)
                tc = bg.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0
                if tc > 0:
                    grand_lome_data.append({
                        'groupe': g,
                        'total_convertis': tc,
                        'bilan_count': bg.count(),
                    })
        else:
            regions_data.append({
                'region': region,
                'total_convertis': total_c,
                'bilan_count': b.count(),
            })

    total_convertis = bilans.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0

    context = {
        'grand_lome_data': grand_lome_data,
        'regions_data': regions_data,
        'total_convertis': total_convertis,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
    }
    return render(request, 'GCK/gck_convertis.html', context)


# ─── Convertis : détail d'une région ──────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_convertis_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    lbl = get_labels(regs)

    bilans = BilanGCK.objects.filter(eglise__region=regs, nouveaux_convertis__gt=0)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    groupes = Groupe.objects.filter(region=regs).order_by('name')
    groupes_data = []
    for g in groupes:
        b = bilans.filter(eglise__groupe=g.name)
        tc = b.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0
        if tc > 0:
            groupes_data.append({
                'groupe': g,
                'total_convertis': tc,
                'bilan_count': b.count(),
            })

    total_convertis = bilans.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0

    context = {
        'region': region,
        'lbl': lbl,
        'groupes_data': groupes_data,
        'total_convertis': total_convertis,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
    }
    return render(request, 'GCK/gck_convertis_region.html', context)


# ─── Convertis : détail d'un groupe ───────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_convertis_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    lbl = get_labels(groupe.region)

    bilans = BilanGCK.objects.filter(eglise__groupe=group, nouveaux_convertis__gt=0)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans, start_date, end_date, mois, jour = _apply_date_filters(bilans, request.GET)

    eglises = Eglise.objects.filter(groupe=group).order_by('nom')
    eglises_data = []
    for e in eglises:
        b = bilans.filter(eglise=e).order_by('-date')
        tc = b.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0
        if tc > 0:
            eglises_data.append({
                'eglise': e,
                'total_convertis': tc,
                'bilan_count': b.count(),
                'bilans': b,
            })

    total_convertis = bilans.aggregate(s=Sum('nouveaux_convertis'))['s'] or 0

    context = {
        'groupe': groupe,
        'lbl': lbl,
        'eglises_data': eglises_data,
        'total_convertis': total_convertis,
        'bilan_count': bilans.count(),
        'start_date': start_date, 'end_date': end_date,
        'mois': mois, 'jour': jour, 'mois_fr': MOIS_FR,
    }
    return render(request, 'GCK/gck_convertis_groupe.html', context)


# ─── Exports ───────────────────────────────────────────────────────────────────

def _export_label(region, groupe, district, start_date, end_date, mois, jour, avec_convertis):
    parts = []
    if region:
        parts.append(f"Région {region}")
    if groupe:
        parts.append(f"Groupe {groupe}")
    if district:
        parts.append(f"{district}")
    if mois:
        mois_noms = dict(MOIS_FR)
        parts.append(mois_noms.get(mois, f"Mois {mois}"))
    if jour:
        parts.append(f"Jour {jour}")
    if start_date and end_date:
        parts.append(f"{start_date} au {end_date}")
    if avec_convertis == '1':
        parts.append("Avec convertis")
    return " — ".join(parts) if parts else "Tous les bilans"


def _export_section_bilans(bilans, totaux, fmt, resource_class, filename, section_title, label):
    """Export générique XLSX/PDF pour les 3 sections GCK (Soir, Conférence, Impact)."""
    if fmt == 'XLS':
        resource = resource_class()
        dataset = resource.export(bilans)
        response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(section_title, styles['Title']),
        Paragraph(label, styles['Normal']),
        Spacer(1, 0.4*cm),
    ]

    header1 = ["Date", "Église", "Groupe", "Région",
               "Adultes", "", "", "Jeunes", "", "", "Enfants", "Total", "Convertis"]
    header2 = ["", "", "", "", "H", "F", "Tot.", "H", "F", "Tot.", "", "", ""]
    data = [header1, header2]

    for b in bilans:
        data.append([
            b.date.strftime("%d/%m/%Y"), b.eglise.nom[:22],
            b.eglise.groupe[:15], b.eglise.region[:12],
            str(b.adultes_hommes), str(b.adultes_femmes), str(b.total_adultes),
            str(b.jeunes_hommes), str(b.jeunes_femmes), str(b.total_jeunes),
            str(b.enfants), str(b.total_participants), str(b.nouveaux_convertis),
        ])
    data.append([
        "TOTAUX", "", "", "",
        str(totaux['total_adultes_h']), str(totaux['total_adultes_f']), str(totaux['total_adultes']),
        str(totaux['total_jeunes_h']), str(totaux['total_jeunes_f']), str(totaux['total_jeunes']),
        str(totaux['total_enfants']), str(totaux['total_participants']), str(totaux['total_convertis']),
    ])

    col_widths = [2.0*cm, 5.0*cm, 3.2*cm, 2.8*cm,
                  1.4*cm, 1.4*cm, 1.6*cm, 1.4*cm, 1.4*cm, 1.6*cm,
                  1.5*cm, 1.6*cm, 1.8*cm]
    table = Table(data, colWidths=col_widths, repeatRows=2)
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)), ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)), ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (4, 0), (6, 0)), ('SPAN', (7, 0), (9, 0)),
        ('SPAN', (10, 0), (10, 1)), ('SPAN', (11, 0), (11, 1)), ('SPAN', (12, 0), (12, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 8),
        ('BACKGROUND', (4, 0), (6, 1), colors.HexColor('#1a3d6b')),
        ('BACKGROUND', (7, 0), (9, 1), colors.HexColor('#4a235a')),
        ('FONTSIZE', (0, 2), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 2), (3, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 2), (-1, -2), [colors.white, colors.HexColor('#f0f4f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    doc.build(elements)
    response.write(buffer.getvalue())
    buffer.close()
    return response


def _export_gck(bilans, totaux, fmt, label):
    return _export_section_bilans(
        bilans, totaux, fmt,
        BilanGCKResource, 'gck_rapport',
        "Croisade Mondiale avec Kumuyi (GCK — Soir)", label
    )


def _export_recapitulatif(dates_data, totaux, moyennes, fmt, label):
    if fmt == 'XLS':
        dataset = Dataset()
        dataset.headers = ['Date', 'Adultes H', 'Adultes F', 'Total Adultes',
                           'Jeunes H', 'Jeunes F', 'Total Jeunes',
                           'Enfants', 'Total', 'Convertis', 'Rapports']
        for d in dates_data:
            dataset.append([
                d['date'].strftime("%d/%m/%Y"),
                d['total_adultes_h'], d['total_adultes_f'], d['total_adultes'],
                d['total_jeunes_h'], d['total_jeunes_f'], d['total_jeunes'],
                d['total_enfants'], d['total_participants'], d['total_convertis'], d['count'],
            ])
        if moyennes:
            dataset.append(['MOYENNES',
                            moyennes['adultes_h'], moyennes['adultes_f'], moyennes['adultes'],
                            moyennes['jeunes_h'], moyennes['jeunes_f'], moyennes['jeunes'],
                            moyennes['enfants'], moyennes['total'], moyennes['convertis'], ''])
        dataset.append(['TOTAUX',
                       totaux['total_adultes_h'], totaux['total_adultes_f'], totaux['total_adultes'],
                       totaux['total_jeunes_h'], totaux['total_jeunes_f'], totaux['total_jeunes'],
                       totaux['total_enfants'], totaux['total_participants'], totaux['total_convertis'],
                       totaux.get('bilan_count', '')])
        response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="gck_recapitulatif.xlsx"'
        return response

    # PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="gck_recapitulatif.pdf"'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("RÉCAPITULATIF GCK — TOGO", styles['Title']))
    elements.append(Paragraph(label, styles['Normal']))
    elements.append(Spacer(1, 0.4*cm))

    header1 = ["Date", "Adultes", "", "", "Jeunes", "", "", "Enfants", "Total", "Convertis", "Rapports"]
    header2 = ["", "H", "F", "Total", "H", "F", "Total", "", "", "", ""]
    data = [header1, header2]
    for d in dates_data:
        data.append([
            d['date'].strftime("%d/%m/%Y"),
            str(d['total_adultes_h']), str(d['total_adultes_f']), str(d['total_adultes']),
            str(d['total_jeunes_h']), str(d['total_jeunes_f']), str(d['total_jeunes']),
            str(d['total_enfants']), str(d['total_participants']), str(d['total_convertis']),
            str(d['count']),
        ])
    if moyennes:
        data.append([
            "MOYENNES",
            str(moyennes['adultes_h']), str(moyennes['adultes_f']), str(moyennes['adultes']),
            str(moyennes['jeunes_h']), str(moyennes['jeunes_f']), str(moyennes['jeunes']),
            str(moyennes['enfants']), str(moyennes['total']), str(moyennes['convertis']), '',
        ])
    data.append([
        "TOTAUX",
        str(totaux['total_adultes_h']), str(totaux['total_adultes_f']), str(totaux['total_adultes']),
        str(totaux['total_jeunes_h']), str(totaux['total_jeunes_f']), str(totaux['total_jeunes']),
        str(totaux['total_enfants']), str(totaux['total_participants']), str(totaux['total_convertis']), '',
    ])

    col_widths = [3*cm, 2*cm, 2*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm]
    table = Table(data, colWidths=col_widths, repeatRows=2)
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (4, 0), (6, 0)),
        ('SPAN', (7, 0), (7, 1)),
        ('SPAN', (8, 0), (8, 1)),
        ('SPAN', (9, 0), (9, 1)),
        ('SPAN', (10, 0), (10, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, 0), (3, 1), colors.HexColor('#1a3d6b')),
        ('BACKGROUND', (4, 0), (6, 1), colors.HexColor('#4a235a')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 2), (-1, -3), [colors.white, colors.HexColor('#f0f4f8')]),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    doc.build(elements)
    response.write(buffer.getvalue())
    buffer.close()
    return response


# ─── Utilitaire ────────────────────────────────────────────────────────────────

def _compute_totaux(bilans):
    agg = bilans.aggregate(
        sum_ah=Sum('adultes_hommes'),
        sum_af=Sum('adultes_femmes'),
        sum_jh=Sum('jeunes_hommes'),
        sum_jf=Sum('jeunes_femmes'),
        sum_e=Sum('enfants'),
        sum_c=Sum('nouveaux_convertis'),
    )
    ah = agg['sum_ah'] or 0
    af = agg['sum_af'] or 0
    jh = agg['sum_jh'] or 0
    jf = agg['sum_jf'] or 0
    e = agg['sum_e'] or 0
    c = agg['sum_c'] or 0
    return {
        'total_adultes_h': ah,
        'total_adultes_f': af,
        'total_adultes': ah + af,
        'total_jeunes_h': jh,
        'total_jeunes_f': jf,
        'total_jeunes': jh + jf,
        'total_enfants': e,
        'total_convertis': c,
        'total_participants': ah + af + jh + jf + e,
    }


# ─── Vue mensuelle combinée (3 sections) ──────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_mensuel(request):
    """Affiche les 3 sections GCK (Soir, Conférence, Impact) pour un mois donné."""
    from datetime import date as dt_date
    from .exports import export_mensuel
    today = dt_date.today()
    region = request.GET.get('region', '')
    groupe = request.GET.get('groupe', '')
    district = request.GET.get('district', '')

    # Si aucun mois explicitement demandé, prendre le dernier mois avec des données
    if 'mois' not in request.GET and 'annee' not in request.GET:
        dernier = (
            BilanGCK.objects.order_by('-date').values_list('date__month', 'date__year').first()
            or (today.month, today.year)
        )
        mois_int, annee_int = dernier[0], dernier[1]
    else:
        try:
            mois_int = int(request.GET.get('mois', today.month))
            annee_int = int(request.GET.get('annee', today.year))
        except (ValueError, TypeError):
            mois_int, annee_int = today.month, today.year

    mois = str(mois_int)
    annee = str(annee_int)

    def _filter(qs):
        qs = filter_by_rbac(request.user, qs, 'bilan')
        qs = qs.filter(date__month=mois_int, date__year=annee_int)
        if region:
            qs = qs.filter(eglise__region__icontains=region)
        if groupe:
            qs = qs.filter(eglise__groupe__icontains=groupe)
        if district:
            qs = qs.filter(eglise__nom__icontains=district)
        return qs

    bilans_soir = _filter(BilanGCK.objects.all()).order_by('eglise__region', 'eglise__nom', '-date')
    bilans_conf = _filter(BilanConferenceMinistres.objects.all()).order_by('eglise__region', 'eglise__nom', '-date')
    bilans_impact = _filter(BilanImpact.objects.all()).order_by('eglise__region', 'eglise__nom', '-date')

    totaux_soir = _compute_totaux(bilans_soir)
    totaux_conf = _compute_totaux(bilans_conf)
    totaux_impact = _compute_totaux(bilans_impact)

    annees = sorted(
        set(
            list(BilanGCK.objects.values_list('date__year', flat=True).distinct()) +
            list(BilanConferenceMinistres.objects.values_list('date__year', flat=True).distinct()) +
            list(BilanImpact.objects.values_list('date__year', flat=True).distinct())
        ), reverse=True
    ) or [today.year]

    mois_noms = dict(MOIS_FR[1:])

    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')

    # Export
    if request.method == 'POST':
        fmt = request.POST.get('file-format', 'PDF')
        mois_label = mois_noms.get(str(mois_int), str(mois_int))
        label_parts = [f"{mois_label} {annee_int}"]
        if region: label_parts.append(f'Région {region}')
        if groupe: label_parts.append(f'Groupe {groupe}')
        if district: label_parts.append(district)
        label_filtre = ' — '.join(label_parts)
        return export_mensuel(
            bilans_soir, totaux_soir,
            bilans_conf, totaux_conf,
            bilans_impact, totaux_impact,
            fmt, mois_label, annee_int, label_filtre,
        )

    return render(request, 'GCK/gck_mensuel.html', {
        'mois': str(mois_int),
        'annee': str(annee_int),
        'mois_fr': MOIS_FR,
        'mois_noms': mois_noms,
        'annees': annees,
        'mois_label': mois_noms.get(str(mois_int), ''),
        'region': region,
        'groupe': groupe,
        'district': district,
        'all_regions': all_regions,
        'all_groupes': all_groupes,
        # Soir
        'bilans_soir': bilans_soir,
        'count_soir': bilans_soir.count(),
        'totaux_soir': totaux_soir,
        # Conférence
        'bilans_conf': bilans_conf,
        'count_conf': bilans_conf.count(),
        'totaux_conf': totaux_conf,
        # Impact
        'bilans_impact': bilans_impact,
        'count_impact': bilans_impact.count(),
        'totaux_impact': totaux_impact,
    })
