from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .models import BilanGCK
from .forms import BilanGCKForm
from .resources import BilanGCKResource
from Eglises.models import Eglise, Groupe, Region
from Membres.utils import filter_by_rbac, RBACMixin, AdminOnlyMixin
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tablib import Dataset


# ─── Ajouter un bilan ──────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_gck(request):
    user = request.user
    avertissement = None

    # Détecter si l'utilisateur est de niveau DISTRICT (un seul district assigné)
    district_unique = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        district_unique = user.profile.district_assigne

    if request.method == 'POST':
        form = BilanGCKForm(request.POST, user=user)
        if form.is_valid():
            eglise_choisie = form.cleaned_data['eglise']
            # Avertir si DISTRICT et église hors périmètre (double vérification)
            if district_unique and district_unique.lower() not in eglise_choisie.nom.lower():
                avertissement = f"⚠️ Attention : vous avez soumis un rapport pour « {eglise_choisie.nom} » alors que votre district assigné est « {district_unique} »."
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
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    avec_convertis = request.GET.get('convertis', '')

    if region:
        bilans = bilans.filter(eglise__region__icontains=region)
    if groupe:
        bilans = bilans.filter(eglise__groupe__icontains=groupe)
    if district:
        bilans = bilans.filter(eglise__nom__icontains=district)
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])
    if avec_convertis == '1':
        bilans = bilans.filter(nouveaux_convertis__gt=0)

    bilans = bilans.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')
    totaux = _compute_totaux(bilans)

    # Export
    if request.method == 'POST':
        fmt = request.POST.get('file-format')
        label = _export_label(region, groupe, district, start_date, end_date, avec_convertis)
        return _export_gck(bilans, totaux, fmt, label)

    # Listes pour les selects de filtres (limitées au périmètre RBAC)
    all_eglises = filter_by_rbac(request.user, Eglise.objects.all(), 'eglise').order_by('nom')
    all_groupes = filter_by_rbac(request.user, Groupe.objects.all(), 'groupe').order_by('name')
    all_regions = filter_by_rbac(request.user, Region.objects.all(), 'region').order_by('name')

    context = {
        'bilans': bilans,
        'bilan_count': bilans.count(),
        'start_date': start_date,
        'end_date': end_date,
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
    bilans = BilanGCK.objects.filter(eglise=eglise)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])

    bilans = bilans.order_by('-date')
    totaux = _compute_totaux(bilans)

    context = {'eglise': eglise, 'bilans': bilans, 'bilan_count': bilans.count(),
                'start_date': start_date, 'end_date': end_date, **totaux}
    return render(request, 'GCK/gck_district.html', context)


# ─── Rapport par Groupe ────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_groupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    bilans = BilanGCK.objects.filter(eglise__groupe=group)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])

    # Compilation par district
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
        **totaux,
    }
    return render(request, 'GCK/gck_groupe.html', context)


# ─── Rapport par Région ────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def gck_region(request, regs):
    region = get_object_or_404(Region, name=regs)
    bilans = BilanGCK.objects.filter(eglise__region=regs)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])

    # Compilation par groupe
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
        **totaux,
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
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])

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
        **totaux,
    }
    return render(request, 'GCK/gck_national.html', context)


# ─── Export ────────────────────────────────────────────────────────────────────

def _export_label(region, groupe, district, start_date, end_date, avec_convertis):
    parts = []
    if region:
        parts.append(f"Région {region}")
    if groupe:
        parts.append(f"Groupe {groupe}")
    if district:
        parts.append(f"District {district}")
    if start_date and end_date:
        parts.append(f"{start_date} au {end_date}")
    if avec_convertis == '1':
        parts.append("Avec convertis")
    return " — ".join(parts) if parts else "Tous les bilans"


def _export_gck(bilans, totaux, fmt, label):
    if fmt == 'XLS':
        resource = BilanGCKResource()
        dataset = resource.export(bilans)
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="gck_export.xls"'
        return response

    if fmt == 'PDF':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="gck_rapport.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                 leftMargin=1*cm, rightMargin=1*cm,
                                 topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        elements.append(Paragraph("Rapport GCK — Croisade Mondiale avec Kumuyi", styles['Title']))
        elements.append(Paragraph(label, styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

        # Tableau principal
        headers = ["Date", "Église", "Groupe", "Région", "Hommes", "Femmes", "Enfants", "Total", "Convertis"]
        data = [headers]
        for b in bilans:
            data.append([
                b.date.strftime("%d/%m/%Y"),
                b.eglise.nom,
                b.eglise.groupe,
                b.eglise.region,
                str(b.hommes),
                str(b.femmes),
                str(b.enfants),
                str(b.total_participants),
                str(b.nouveaux_convertis),
            ])
        # Ligne totaux
        data.append([
            "TOTAL", "", "", "",
            str(totaux['total_hommes']),
            str(totaux['total_femmes']),
            str(totaux['total_enfants']),
            str(totaux['total_participants']),
            str(totaux['total_convertis']),
        ])

        col_widths = [2.2*cm, 5*cm, 3.5*cm, 3.5*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2.2*cm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        doc.build(elements)
        response.write(buffer.getvalue())
        buffer.close()
        return response


# ─── Utilitaire ────────────────────────────────────────────────────────────────

def _compute_totaux(bilans):
    agg = bilans.aggregate(
        total_hommes=Sum('hommes'),
        total_femmes=Sum('femmes'),
        total_enfants=Sum('enfants'),
        total_convertis=Sum('nouveaux_convertis'),
    )
    h = agg['total_hommes'] or 0
    f = agg['total_femmes'] or 0
    e = agg['total_enfants'] or 0
    c = agg['total_convertis'] or 0
    return {
        'total_hommes': h,
        'total_femmes': f,
        'total_enfants': e,
        'total_convertis': c,
        'total_participants': h + f + e,
    }
