from django.shortcuts import render, redirect, get_object_or_404
from .models import Seance, Bilan 
from .forms import BilanForm, DateRangeForm
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView 
from django.urls import reverse_lazy
from django.db.models import Sum
from Eglises.models import Groupe, Region, Eglise
from Membres.utils import filter_by_rbac

from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .models import Bilan
from .resources import BilanResource, GroupeResource




def seances(request):
    bilans = Bilan.objects.all()
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    
    # Filtrage avancé
    region = request.GET.get('region')
    groupe = request.GET.get('groupe')
    district = request.GET.get('district')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if region:
        bilans = bilans.filter(eglise__region__icontains=region)
    if groupe:
        bilans = bilans.filter(eglise__groupe__icontains=groupe)
    if district:
        bilans = bilans.filter(eglise__nom__icontains=district)
    
    if start_date and end_date:
        bilans = bilans.filter(date__range=[start_date, end_date])
    
    # Ordonner par Région, puis Groupe, puis Église pour le rapport national
    bilans = bilans.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')
    
    bilan_count = bilans.count()
    total_assistance_globale = sum(b.total_assistance for b in bilans)
    total_cotisation_globale = sum(b.cotisation for b in bilans)
    
    resource = BilanResource()

    if request.method == 'POST':
        file_format = request.POST.get('file-format')
        dataset = resource.export(bilans)

        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="seances_export.csv"'
            return response
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="seances_export.json"'
            return response
        elif file_format == 'XLS':
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="seances_export.xlsx"'
            return response
        elif file_format == 'PDF':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="seances_rapport.pdf"'

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                     leftMargin=1*cm, rightMargin=1*cm,
                                     topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Rapport des Bilans de Séances", styles['Title']))
            elements.append(Spacer(1, 0.4*cm))

            headers = ["Date", "Église", "Séance", "Groupe", "Région",
                       "Ad. H", "Ad. F", "J. G", "J. F", "Enf. G", "Enf. F",
                       "Total H", "Total F", "Assistance", "Cotisation"]
            data = [headers]
            total_assistance = 0
            total_cotisation = 0
            for b in bilans:
                data.append([
                    b.date.strftime("%d/%m/%Y"),
                    b.eglise.nom,
                    b.seance.type,
                    b.eglise.groupe,
                    b.eglise.region,
                    str(b.adultes_hommes), str(b.adultes_femmes),
                    str(b.jeunes_garcons), str(b.jeunes_filles),
                    str(b.enfants_garcons), str(b.enfants_filles),
                    str(b.total_hommes), str(b.total_femmes),
                    str(b.total_assistance), str(b.cotisation),
                ])
                total_assistance += b.total_assistance
                total_cotisation += b.cotisation

            data.append(["TOTAL", "", "", "", "", "", "", "", "", "", "",
                          "", "", str(total_assistance), str(total_cotisation)])

            col_w = [2*cm, 4*cm, 2*cm, 2.8*cm, 2.8*cm,
                     1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm,
                     1.5*cm, 1.5*cm, 1.8*cm, 2*cm]
            table = Table(data, colWidths=col_w, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f4ff')]),
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
    
    
    return render(request, 'seances/seances.html', {
        'bilans': bilans, 
        'bilan_count': bilan_count,
        'total_assistance_globale': total_assistance_globale,
        'total_cotisation_globale': total_cotisation_globale,
    })


def add_bilan(request):
    user = request.user
    district_unique = None
    if hasattr(user, 'profile') and user.profile.niveau_acces == 'DISTRICT' and user.profile.district_assigne:
        district_unique = user.profile.district_assigne

    if request.method == 'POST':
        form = BilanForm(request.POST, user=user)
        if form.is_valid():
            bilan = form.save()
            return redirect('seance_details', id=bilan.id)
    else:
        form = BilanForm(user=user)
    return render(request, 'seances/add_seance.html', {
        'form': form,
        'district_unique': district_unique,
    })

def seance_details(request, id):
    bilan = get_object_or_404(Bilan, pk=id) 
    return render(request, 'seances/seance_details.html', {'bilan': bilan})

class EditSeance(UpdateView):
    model = Bilan
    form_class = BilanForm
    template_name = 'seances/edit_seances.html'
    context_object_name = 'bilan'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class DeleteSeance(DeleteView):
    model = Bilan
    template_name = 'seances/delete_seance.html'
    context_object_name = 'bilan'
    success_url = reverse_lazy('seances')


''' 
def seance_filter_jour(request, seance_type):
    seances = Seance.objects.filter(type=seance_type)
    data = []

    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0
    seance_filter_count = 0

    for seance in seances:
        bilans = Bilan.objects.filter(seance=seance)
        seance_filter_count += bilans.count()
        for bilan in bilans:
            total_hommes += bilan.adultes_hommes + bilan.jeunes_garcons + bilan.enfants_garcons
            total_femmes += bilan.adultes_femmes + bilan.jeunes_filles + bilan.enfants_filles
            total_assistance += (bilan.adultes_hommes + bilan.adultes_femmes +
                                bilan.jeunes_garcons + bilan.jeunes_filles +
                                bilan.enfants_garcons + bilan.enfants_filles)
            total_cotisation += bilan.cotisation
            data.append({
                'date': bilan.date,
                'eglise': bilan.eglise,
                'adultes_hommes': bilan.adultes_hommes,
                'adultes_femmes': bilan.adultes_femmes,
                'jeunes_garcons': bilan.jeunes_garcons,
                'jeunes_filles': bilan.jeunes_filles,
                'enfants_garcons': bilan.enfants_garcons,
                'enfants_filles': bilan.enfants_filles,
                'cotisation': bilan.cotisation,
            })

    context = {
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
        'seance_filter_count':seance_filter_count
    }

    return render(request, 'seances/seance_filter.html', context)

 '''



def group_view(request):
    groupes = Groupe.objects.all()
    groupes = filter_by_rbac(request.user, groupes, 'groupe')
    data = []
    
    # Définir l'ordre des jours
    order_of_days = ["Lundi", "Jeudi", "Dimanche"]
    
    if request.method == 'POST':
        file_format = request.POST.get('file-format')

        # Export en CSV, Excel, ou PDF
        resource = GroupeResource()
        dataset = resource.export(groupes)

        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="groupes.csv"'
            return response        
        elif file_format == 'XLS':
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="groupes.xlsx"'
            return response
        elif file_format == 'PDF':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="groupes.pdf"'

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            table_data = [["Groupe", "Total Hommes", "Total Femmes", "Total Assistance", "Total Cotisation", "Jours de Séance"]]
            for item in data:
                table_data.append([item['groupe'].name, item['total_hommes'], item['total_femmes'], item['total_assistance'],
                                   item['total_cotisation'], ", ".join(item['seances_jour'])])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)
            doc.build(elements)

            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        
    

    for groupe in groupes:
        bilans = Bilan.objects.filter(eglise__groupe=groupe)
        bilan_groupe_count = bilans.count()
        total_hommes = bilans.aggregate(Sum('adultes_hommes'))['adultes_hommes__sum'] or 0
        total_femmes = bilans.aggregate(Sum('adultes_femmes'))['adultes_femmes__sum'] or 0
        total_jeunes_garcons = bilans.aggregate(Sum('jeunes_garcons'))['jeunes_garcons__sum'] or 0
        total_jeunes_filles = bilans.aggregate(Sum('jeunes_filles'))['jeunes_filles__sum'] or 0
        total_enfants_garcons = bilans.aggregate(Sum('enfants_garcons'))['enfants_garcons__sum'] or 0
        total_enfants_filles = bilans.aggregate(Sum('enfants_filles'))['enfants_filles__sum'] or 0
        total_cotisation = bilans.aggregate(Sum('cotisation'))['cotisation__sum'] or 0

        total_assistance = (total_hommes + total_femmes +
                            total_jeunes_garcons + total_jeunes_filles +
                            total_enfants_garcons + total_enfants_filles)
        
        # Récupérer un ensemble unique de jours de séance
        #seances_jour = bilans.values_list('seance__type', flat=True).distinct()
        
        # Utilisation d'un set pour les jours de séance uniques
        seances_jour_set = set(bilans.values_list('seance__type', flat=True).distinct())
        # Trier les jours de séance selon l'ordre souhaité
        seances_jour_sorted = sorted(seances_jour_set, key=lambda day: order_of_days.index(day))
        

        data.append({
            'groupe': groupe,
            'total_hommes': total_hommes + total_jeunes_garcons + total_enfants_garcons,
            'total_femmes': total_femmes + total_jeunes_filles + total_enfants_filles,
            'total_assistance': total_assistance,
            'total_cotisation': total_cotisation,
            'bilan_groupe_count': bilan_groupe_count,
            #'seances_jour': seances_jour,
            'seances_jour':seances_jour_set
        })
    
    # Debugging output
    print("Data being sent to template:", data)

    return render(request, 'seances/group_totals.html', {'data': data})



''' 
def group_seance_filter(request, groupe_id, seance_type):
    groupe = Groupe.objects.get(id=groupe_id)
    bilans = Bilan.objects.filter(eglise__groupe=groupe, seance__type=seance_type)

    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0

    data = []

    for bilan in bilans:
        hommes = bilan.adultes_hommes + bilan.jeunes_garcons + bilan.enfants_garcons
        femmes = bilan.adultes_femmes + bilan.jeunes_filles + bilan.enfants_filles
        assistance = hommes + femmes
        cotisation = bilan.cotisation

        total_hommes += hommes
        total_femmes += femmes
        total_assistance += assistance
        total_cotisation += cotisation

        data.append({
            'date': bilan.date,
            'eglise': bilan.eglise,
            'adultes_hommes': bilan.adultes_hommes,
            'jeunes_garcons': bilan.jeunes_garcons,
            'enfants_garcons': bilan.enfants_garcons,
            'adultes_femmes': bilan.adultes_femmes,
            'jeunes_filles': bilan.jeunes_filles,
            'enfants_filles': bilan.enfants_filles,
            'hommes': hommes,
            'femmes': femmes,
            'assistance': assistance,
            'cotisation': cotisation,
        })

    context = {
        'groupe': groupe,
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
    }

    return render(request, 'seances/group_seance_filter.html', context)

 '''

''' 
def region_view(request):
    regions = Region.objects.all()
    data = []

    for region in regions:
        bilans = Bilan.objects.filter(eglise__region=region)
        region_totals = {
            'region_id': region.id,
            'region': region.name,
            'total_hommes': bilans.aggregate(Sum('adultes_hommes'))['adultes_hommes__sum'] or 0,
            'total_femmes': bilans.aggregate(Sum('adultes_femmes'))['adultes_femmes__sum'] or 0,
            'total_jeunes_garcons': bilans.aggregate(Sum('jeunes_garcons'))['jeunes_garcons__sum'] or 0,
            'total_jeunes_filles': bilans.aggregate(Sum('jeunes_filles'))['jeunes_filles__sum'] or 0,
            'total_enfants_garcons': bilans.aggregate(Sum('enfants_garcons'))['enfants_garcons__sum'] or 0,
            'total_enfants_filles': bilans.aggregate(Sum('enfants_filles'))['enfants_filles__sum'] or 0,
            'total_cotisation': bilans.aggregate(Sum('cotisation'))['cotisation__sum'] or 0,
            'seances_jour': bilans.values_list('seance__type', flat=True).distinct(),
        }

        data.append(region_totals)

    return render(request, 'seances/region_totals.html', {'data': data})

 '''

''' 
def region_seance_filter(request, region_name, seance_type):
    # Filtrer les groupes par région
    groupes = Groupe.objects.filter(region=region_name)
    
    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0
    seance_filter_count = 0

    data = []

    for groupe in groupes:
        # Filtrer les bilans par groupe et type de séance
        bilans = Bilan.objects.filter(eglise__groupe=groupe.name, seance__type=seance_type)

        groupe_total_hommes = bilans.aggregate(Sum('adultes_hommes'))['adultes_hommes__sum'] or 0
        groupe_total_femmes = bilans.aggregate(Sum('adultes_femmes'))['adultes_femmes__sum'] or 0
        groupe_total_jeunes_garcons = bilans.aggregate(Sum('jeunes_garcons'))['jeunes_garcons__sum'] or 0
        groupe_total_jeunes_filles = bilans.aggregate(Sum('jeunes_filles'))['jeunes_filles__sum'] or 0
        groupe_total_enfants_garcons = bilans.aggregate(Sum('enfants_garcons'))['enfants_garcons__sum'] or 0
        groupe_total_enfants_filles = bilans.aggregate(Sum('enfants_filles'))['enfants_filles__sum'] or 0
        groupe_total_cotisation = bilans.aggregate(Sum('cotisation'))['cotisation__sum'] or 0

        groupe_total_assistance = (groupe_total_hommes + groupe_total_femmes +
                                   groupe_total_jeunes_garcons + groupe_total_jeunes_filles +
                                   groupe_total_enfants_garcons + groupe_total_enfants_filles)

        total_hommes += groupe_total_hommes + groupe_total_jeunes_garcons + groupe_total_enfants_garcons
        total_femmes += groupe_total_femmes + groupe_total_jeunes_filles + groupe_total_enfants_filles
        total_assistance += groupe_total_assistance
        total_cotisation += groupe_total_cotisation
        seance_filter_count += bilans.count()

        data.append({
            'groupe': groupe.name,
            'total_hommes': groupe_total_hommes + groupe_total_jeunes_garcons + groupe_total_enfants_garcons,
            'total_femmes': groupe_total_femmes + groupe_total_jeunes_filles + groupe_total_enfants_filles,
            'total_assistance': groupe_total_assistance,
            'total_cotisation': groupe_total_cotisation,
        })

    context = {
        'region_name': region_name,
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
        'seance_filter_count': seance_filter_count
    }

    return render(request, 'seances/region_seance_filter.html', context)


 '''

def region_view(request):
    regions = Region.objects.all()
    regions = filter_by_rbac(request.user, regions, 'region')
    data = []

    for region in regions:
        bilans = Bilan.objects.filter(eglise__region=region)
        
        # Utilisation d'un set pour les jours de séance uniques
        seances_jour_set = set(bilans.values_list('seance__type', flat=True).distinct())
        
        region_totals = {
            'region_id': region.id,
            'region': region.name,
            'total_hommes': bilans.aggregate(Sum('adultes_hommes'))['adultes_hommes__sum'] or 0,
            'total_femmes': bilans.aggregate(Sum('adultes_femmes'))['adultes_femmes__sum'] or 0,
            'total_jeunes_garcons': bilans.aggregate(Sum('jeunes_garcons'))['jeunes_garcons__sum'] or 0,
            'total_jeunes_filles': bilans.aggregate(Sum('jeunes_filles'))['jeunes_filles__sum'] or 0,
            'total_enfants_garcons': bilans.aggregate(Sum('enfants_garcons'))['enfants_garcons__sum'] or 0,
            'total_enfants_filles': bilans.aggregate(Sum('enfants_filles'))['enfants_filles__sum'] or 0,
            'total_cotisation': bilans.aggregate(Sum('cotisation'))['cotisation__sum'] or 0,
            'seances_jour': seances_jour_set,
        }

        data.append(region_totals)

    return render(request, 'seances/region_totals.html', {'data': data})


def filter_seances(queryset, start_date, end_date):
    if start_date and end_date:
        return queryset.filter(date__range=(start_date, end_date))
    elif start_date:
        return queryset.filter(date__gte=start_date)
    elif end_date:
        return queryset.filter(date__lte=end_date)
    return queryset

def seance_filter_jour(request, seance_type):
    form = DateRangeForm(request.GET)
    start_date = None
    end_date = None

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

    seances = Seance.objects.filter(type=seance_type)
    bilans = Bilan.objects.filter(seance__in=seances)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans = filter_seances(bilans, start_date, end_date)
    data = []

    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0
    seance_filter_count = 0

    for seance in seances:
        # Note: filtering is already done on the full queryset for efficiency
        # We just iterate over the pre-filtered bilans if needed, but let's re-align the logic
        pass

    seance_filter_count = bilans.count()
    for bilan in bilans:
            total_hommes += bilan.adultes_hommes + bilan.jeunes_garcons + bilan.enfants_garcons
            total_femmes += bilan.adultes_femmes + bilan.jeunes_filles + bilan.enfants_filles
            total_assistance += (bilan.adultes_hommes + bilan.adultes_femmes +
                                bilan.jeunes_garcons + bilan.jeunes_filles +
                                bilan.enfants_garcons + bilan.enfants_filles)
            total_cotisation += bilan.cotisation
            data.append({
                'date': bilan.date,
                'eglise': bilan.eglise,
                'adultes_hommes': bilan.adultes_hommes,
                'adultes_femmes': bilan.adultes_femmes,
                'jeunes_garcons': bilan.jeunes_garcons,
                'jeunes_filles': bilan.jeunes_filles,
                'enfants_garcons': bilan.enfants_garcons,
                'enfants_filles': bilan.enfants_filles,
                'cotisation': bilan.cotisation,
            })

    context = {
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
        'seance_filter_count': seance_filter_count,
        'form': form
    }

    return render(request, 'seances/seance_filter.html', context)

def group_seance_filter(request, groupe_id, seance_type):
    form = DateRangeForm(request.GET)
    start_date = None
    end_date = None

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

    groupe = Groupe.objects.get(id=groupe_id)
    bilans = Bilan.objects.filter(eglise__groupe=groupe, seance__type=seance_type)
    bilans = filter_by_rbac(request.user, bilans, 'bilan')
    bilans = filter_seances(bilans, start_date, end_date)

    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0

    data = []

    for bilan in bilans:
        hommes = bilan.adultes_hommes + bilan.jeunes_garcons + bilan.enfants_garcons
        femmes = bilan.adultes_femmes + bilan.jeunes_filles + bilan.enfants_filles
        assistance = hommes + femmes
        cotisation = bilan.cotisation

        total_hommes += hommes
        total_femmes += femmes
        total_assistance += assistance
        total_cotisation += cotisation

        data.append({
            'date': bilan.date,
            'eglise': bilan.eglise,
            'adultes_hommes': bilan.adultes_hommes,
            'jeunes_garcons': bilan.jeunes_garcons,
            'enfants_garcons': bilan.enfants_garcons,
            'adultes_femmes': bilan.adultes_femmes,
            'jeunes_filles': bilan.jeunes_filles,
            'enfants_filles': bilan.enfants_filles,
            'hommes': hommes,
            'femmes': femmes,
            'assistance': assistance,
            'cotisation': cotisation,
        })

    context = {
        'groupe': groupe,
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
        'form': form
    }

    return render(request, 'seances/group_seance_filter.html', context)

def region_seance_filter(request, region_name, seance_type):
    form = DateRangeForm(request.GET)
    start_date = None
    end_date = None

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

    groupes = Groupe.objects.filter(region=region_name)
    
    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0
    seance_filter_count = 0

    data = []

    for groupe in groupes:
        bilans = Bilan.objects.filter(eglise__groupe=groupe.name, seance__type=seance_type)
        bilans = filter_by_rbac(request.user, bilans, 'bilan')
        bilans = filter_seances(bilans, start_date, end_date)

        groupe_total_hommes = bilans.aggregate(Sum('adultes_hommes'))['adultes_hommes__sum'] or 0
        groupe_total_femmes = bilans.aggregate(Sum('adultes_femmes'))['adultes_femmes__sum'] or 0
        groupe_total_jeunes_garcons = bilans.aggregate(Sum('jeunes_garcons'))['jeunes_garcons__sum'] or 0
        groupe_total_jeunes_filles = bilans.aggregate(Sum('jeunes_filles'))['jeunes_filles__sum'] or 0
        groupe_total_enfants_garcons = bilans.aggregate(Sum('enfants_garcons'))['enfants_garcons__sum'] or 0
        groupe_total_enfants_filles = bilans.aggregate(Sum('enfants_filles'))['enfants_filles__sum'] or 0
        groupe_total_cotisation = bilans.aggregate(Sum('cotisation'))['cotisation__sum'] or 0

        groupe_total_assistance = (groupe_total_hommes + groupe_total_femmes +
                                   groupe_total_jeunes_garcons + groupe_total_jeunes_filles +
                                   groupe_total_enfants_garcons + groupe_total_enfants_filles)

        total_hommes += groupe_total_hommes + groupe_total_jeunes_garcons + groupe_total_enfants_garcons
        total_femmes += groupe_total_femmes + groupe_total_jeunes_filles + groupe_total_enfants_filles
        total_assistance += groupe_total_assistance
        total_cotisation += groupe_total_cotisation
        seance_filter_count += bilans.count()

        data.append({
            'groupe': groupe.name,
            'total_hommes': groupe_total_hommes + groupe_total_jeunes_garcons + groupe_total_enfants_garcons,
            'total_femmes': groupe_total_femmes + groupe_total_jeunes_filles + groupe_total_enfants_filles,
            'total_assistance': groupe_total_assistance,
            'total_cotisation': groupe_total_cotisation,
        })

    context = {
        'region_name': region_name,
        'seance_type': seance_type,
        'data': data,
        'total_hommes': total_hommes,
        'total_femmes': total_femmes,
        'total_assistance': total_assistance,
        'total_cotisation': total_cotisation,
        'seance_filter_count': seance_filter_count,
        'form': form
    }

    return render(request, 'seances/region_seance_filter.html', context)






