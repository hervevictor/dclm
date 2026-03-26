from django.shortcuts import render, redirect, get_object_or_404
from .models import Seance, Bilan 
from .forms import BilanForm, DateRangeForm
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView 
from django.urls import reverse_lazy
from django.db.models import Sum
from Eglises.models import Groupe, Region, Eglise

from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from .models import Bilan
from .resources import BilanResource, GroupeResource




def seances(request):
    bilans = Bilan.objects.all()
    bilan_count = bilans.count()
    
    resource = BilanResource()

    if request.method == 'POST':
        file_format = request.POST['file-format']
        dataset = resource.export(bilans)

        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="bilans.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="bilans.json"'
            return response
        elif file_format == 'PDF':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="bilans.pdf"'

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            data = [["Date", "Église", "Adultes Hommes", "Adultes Femmes", "Jeunes Garçons", "Jeunes Filles", "Enfants Garçons", "Enfants Filles", "Cotisation"]]
            for bilan in bilans:
                data.append([bilan.date, bilan.eglise.nom, bilan.adultes_hommes, bilan.adultes_femmes,
                             bilan.jeunes_garcons, bilan.jeunes_filles, bilan.enfants_garcons, bilan.enfants_filles, bilan.cotisation])

            table = Table(data)
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
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="bilans.xls"'
            return response
    
    
    return render(request, 'seances/seances.html', {'bilans': bilans, 'bilan_count':bilan_count})


def add_bilan(request):
    if request.method == 'POST':
        form = BilanForm(request.POST)
        if form.is_valid():
            bilan = form.save()
            return redirect('seance_details', id=bilan.id)
    else:
        form = BilanForm()
    return render(request, 'seances/add_seance.html', {'form': form})

def seance_details(request, id):
    bilan = get_object_or_404(Bilan, pk=id) 
    return render(request, 'seances/seance_details.html', {'bilan': bilan})

class EditSeance(UpdateView):
    model = Bilan
    form_class = BilanForm
    template_name = 'seances/edit_seances.html'
    context_object_name = 'bilan'

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
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="groupes.xls"'
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
    data = []

    total_hommes = 0
    total_femmes = 0
    total_assistance = 0
    total_cotisation = 0
    seance_filter_count = 0

    for seance in seances:
        bilans = Bilan.objects.filter(seance=seance)
        bilans = filter_seances(bilans, start_date, end_date)
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






