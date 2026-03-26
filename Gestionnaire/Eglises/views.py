from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Eglise, Groupe, Region
from .forms import EgliseForm, GroupeForm
from django.urls import reverse_lazy

from Adultes.resources import EgliseResources
from django.http import HttpResponse
from tablib import Dataset
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from Jeunes_app.models import Jeune
from Adultes.models import Adulte 
from Enfants.models import Enfant

from Annonces.models import Message, Annonce
from datetime import timedelta
from django.utils import timezone



def index(request):
    # Calculer la date limite du message
    date_limit = timezone.now().date() - timedelta(days=6)
    
    #annonce date limite
    date_limit = timezone.now().date() - timedelta(days=15)
    
    
    # Filtrer les messages plus récents que la date limite
    recent_messages = Message.objects.filter(date__gt=date_limit).order_by('-date')
    
    # Filtrer les annnces plus récents que la date limite
    recent_annonces = Annonce.objects.filter(add_date__gt=date_limit).order_by('-add_date')
    
    
    
    # Prendre le message le plus récent
    if recent_messages.exists():
        message = recent_messages.first()
    else:
        message = None
    
    # Prendre le annonce le plus récent
    if recent_annonces.exists():
        annonce = recent_annonces.first()
    else:
        annonce = None
    return render(request, 'index.html', {'message':message, 'annonce':annonce})


def dashboard(request):
    eglises = Eglise.objects.all().count()
    groupes = Groupe.objects.all().count()
    regions = Region.objects.all().count()
    adultes = Adulte.objects.all().count()
    jeunes = Jeune.objects.all().count()
    enfants = Enfant.objects.all().count()
    
    context = {
        'eglises':eglises,
        'groupes':groupes,
        'regions':regions,
        'adultes':adultes,
        'jeunes':jeunes,
        'enfants':enfants
    }
    return render(request, 'dashboard.html', context)



class AddEglise(CreateView):
    model = Eglise 
    #fields = '__all__'
    form_class = EgliseForm
    template_name = 'Eglises/add_eglise.html'


class EgliseList(ListView):
    model = Eglise 
    template_name = 'Eglises/eglise_liste.html'
    
    def get_context_data(self, *args, **kwargs):
        eglises_nombre = Eglise.objects.all().count()
        context = super(EgliseList, self).get_context_data(*args, **kwargs)
        context["eglises_nombre"] = eglises_nombre
        return context
    
class EgliseDetails(DetailView):
    model = Eglise 
    template_name = 'Eglises/eglise_details.html'
 
class EditEglise(UpdateView):
    model = Eglise 
    #fields = '__all__'
    form_class = EgliseForm
    template_name = 'Eglises/edit_Eglise.html'   
    
class DeleteEglise(DeleteView):
    model = Eglise 
    template_name = 'Eglises/delete_Eglise.html'
    success_url = reverse_lazy('eglises')


# Search eglise se trouve dans annonce pour raison d'erreurs infondées
    

def EgliseGroupe(request, group):
    groupes = Groupe.objects.all()
    eglises = Eglise.objects.filter(groupe=group)
    eglise_nombre = eglises.count()
    
    resource = EgliseResources()
    
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        dataset = resource.export(eglises)
        
        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
            return response
        elif file_format == 'PDF':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="eglises_.pdf"'
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Table data
            data = [["Nom", "Pasteur", "Dirigeant J", "Dirigeant E", "groupe", "Region", 'N membres', 'telephone']]
            for eglise in eglises:
                data.append([eglise.nom, eglise.nom_du_pasteur, eglise.nom_du_dirigeant_des_jeunes, eglise.nom_du_dirigeant_des_enfants, eglise.groupe, eglise.region, eglise.nombre_de_membres, eglise.telephone])

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
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
            response['Content-Disposition'] = 'attachment; filename="exported_data.xls"'
            return response
    
    context = {
        'eglises' : eglises,
        'eglise_nombre' : eglise_nombre,
        'groupes' : groupes,
        'group' : group
    }
    return render(request, 'Eglises/eglise_groupe.html', context)


def EgliseRegion(request, regs):
    region = Region.objects.all()
    eglises = Eglise.objects.filter(region=regs)
    eglise_nombre = eglises.count()
    
    context = {
        'eglises' : eglises,
        'eglise_nombre' : eglise_nombre,
        'regs' : regs
    }
    return render(request, 'Eglises/eglise_region.html', context)



''' Groupes '''

def AddGroupe(request):
    form = GroupeForm()
    if request.method == 'POST':
        form = GroupeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('groupe_liste')
        
    context = {
        'form' : form
    }
    return render(request, 'Groupes/add_groupe.html', context)

class AddGroupe(CreateView):
    model = Groupe 
    #fields = '__all__'
    form_class = GroupeForm
    template_name = 'Groupes/add_groupe.html'
    

def Groupes(request):
    groupes = Groupe.objects.all()
    groupes_nombre = groupes.count()
    
    context = {
        'groupes' : groupes,
        'groupes_nombre' : groupes_nombre
    }
    return render(request, 'Groupes/groupe_liste.html', context)

def groupeDetails(request, id):
    #groupe = Groupe.objects.filter(pk=id)
    groupe = get_object_or_404(Groupe, pk=id)
    context = {
        'groupe' : groupe,
    }
    return render(request, 'Groupes/groupe_details.html', context)

def EditGroupe(request, pk):
    groupe = Groupe.objects.get(id=pk)
    form = GroupeForm(instance=groupe)
    if request.method == 'POST':
        form = GroupeForm(request.POST, instance=groupe)
        if form.is_valid():
            form.save()
            return redirect('groupe_details', id=groupe.pk)
    
    context = {
        'form' : form,
        'groupe' : groupe,
    }
    return render(request, 'Groupes/edit_groupe.html', context)

def DeleteGroupe(request, pk):
    groupe = Groupe.objects.get(id=pk)
    if request.method == 'POST':
        groupe.delete()
        return redirect('groupe_liste')
    
    context = {
        'groupe': groupe,
    }
    return render(request, 'Groupes/delete_groupe.html', context)

 
def FiltreGroupeRegion(request, regs):
    groupe_region = Groupe.objects.filter(region=regs)
    groupe_region_count = groupe_region.count()
    context = {
        'groupe_region':groupe_region,
        'groupe_region_count':groupe_region_count,
        'regs':regs
    }
    return render(request, 'Groupes/groupe_region.html', context)


