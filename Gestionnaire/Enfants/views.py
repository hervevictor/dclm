from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Enfant 
from django.urls import reverse_lazy
from .forms import  EnfantForm
from Eglises.models import Eglise, Region, Groupe 
from Membres.utils import filter_by_rbac


from Adultes.resources import EnfantResources
from django.http import HttpResponse
from tablib import Dataset
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors



''' Enfants '''


class AddEnfant(CreateView):
    model = Enfant 
    form_class = EnfantForm
    template_name = 'Enfants/add_enfant.html'


class EnfantList(ListView):
    model = Enfant 
    template_name = 'Enfants/enfant_liste.html'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return filter_by_rbac(self.request.user, qs, 'enfant')
        
    def get_context_data(self, *args, **kwargs):
        context = super(EnfantList, self).get_context_data(*args, **kwargs)
        context["enfants"] = self.get_queryset().count()
        return context


class EnfantDetails(DetailView):
    model = Enfant 
    template_name = 'Enfants/enfant_details.html'
 
class EditEnfant(UpdateView):
    model = Enfant 
    form_class = EnfantForm
    template_name = 'Enfants/edit_enfant.html'   
    
class DeleteEnfant(DeleteView):
    model = Enfant 
    template_name = 'Enfants/delete_enfant.html'
    success_url = reverse_lazy('enfants')
    



 
     
def FilteEnfantsDistrict(request, dist):
    eglise = get_object_or_404(Eglise, pk=dist)
    enfants_district = Enfant.objects.filter(eglise=dist)
    enfants_district = filter_by_rbac(request.user, enfants_district, 'enfant')
    enfants_district_nombre = enfants_district.count()
    
    
    resource = EnfantResources()
    
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        dataset = resource.export(enfants_district)
        
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
            response['Content-Disposition'] = f'attachment; filename="enfants_district_{eglise.nom}.pdf"'
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Table data
            data = [["Nom", "Prénom", "Classe", "Date de Naissance", "Avec qui vit-il", "Contact P/T", "Sexe", "District"]]
            for enfant in enfants_district:
                data.append([enfant.nom, enfant.prenom, enfant.classe, enfant.date_de_naissance.strftime("%Y-%m-%d"), enfant.avec_qui_vit_il,  enfant.contact, enfant.sexe, enfant.eglise])

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
        'enfants_district': enfants_district,
        'enfants_district_nombre': enfants_district_nombre,
        'eglise': eglise
    }
    return render(request, 'Enfants/enfants_district.html', context)
 
    
def FilteEnfantsRegion(request, regs):
    region = get_object_or_404(Region, name=regs)
    enfants_region = Enfant.objects.filter(eglise__region=region)
    enfants_region = filter_by_rbac(request.user, enfants_region, 'enfant')
    enfants_region_nombre = enfants_region.count()
    
    context = {
        'enfants_region' : enfants_region,
        'enfants_region_nombre':enfants_region_nombre,
        'region' : region,
        'regs':regs
    }
    return render(request, 'Enfants/enfants_region.html', context)


def FilteEnfantsGroupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    enfants_groupe = Enfant.objects.filter(eglise__groupe=groupe)
    enfants_groupe = filter_by_rbac(request.user, enfants_groupe, 'enfant')
    enfants_groupe_nombre = enfants_groupe.count()
    
    context = {
        'enfants_groupe': enfants_groupe,
        'enfants_groupe_nombre': enfants_groupe_nombre,
        'group': group,
        'groupe':groupe
         
    }
    return render(request, 'Enfants/enfants_groupe.html', context)    


def SearchEnfants(request):
    if request.method == 'POST':
        search_enfant = request.POST['search_enfant'] 
        search_enfants = Enfant.objects.filter(nom__contains=search_enfant)
        search_enfant_count = search_enfants.count()
        
        context = {
            'search_enfant':search_enfant,
            'search_enfants':search_enfants,
            'search_enfant_count':search_enfant_count,
        }
        return render(request, 'Enfants/search_enfant.html', context)


    
