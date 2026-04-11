from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Adulte
from django.urls import reverse_lazy
from .forms import AdulteForm
from Eglises.models import Eglise, Region, Groupe
from Membres.utils import filter_by_rbac

from .resources import AdulteResources
from django.http import HttpResponse
from tablib import Dataset
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
 

class AddAdulte(CreateView):
    model = Adulte 
    #fields = '__all__'
    form_class = AdulteForm
    template_name = 'Adultes/add_adulte.html'


class AdulteList(ListView):
    model = Adulte 
    template_name = 'Adultes/adulte_liste.html'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return filter_by_rbac(self.request.user, qs, 'adulte')
        
    def get_context_data(self, *args, **kwargs):
        context = super(AdulteList, self).get_context_data(*args, **kwargs)
        context["adultes"] = self.get_queryset().count()
        return context

class AdulteDetails(DetailView):
    model = Adulte 
    template_name = 'Adultes/adulte_details.html'
 
class EditAdulte(UpdateView):
    model = Adulte 
    form_class = AdulteForm
    template_name = 'Adultes/edit_adulte.html'   
    
class DeleteAdulte(DeleteView):
    model = Adulte 
    template_name = 'Adultes/delete_adulte.html'
    success_url = reverse_lazy('adultes')

  
     
def FilteAdultesDistrict(request, dist):
    eglise = get_object_or_404(Eglise, pk=dist)
    adultes_district = Adulte.objects.filter(eglise=dist)
    adultes_district = filter_by_rbac(request.user, adultes_district, 'adulte')
    adultes_district_nombre = adultes_district.count()
    
    resource = AdulteResources()
    
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        dataset = resource.export(adultes_district)
        
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
            response['Content-Disposition'] = f'attachment; filename="adultes_district_{eglise.nom}.pdf"'
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Table data
            data = [["Nom", "Prénom", "Profession", "Date de naissance", "Role", "Contact", "Baptiser", "Status M", "Sexe"]]
            for adulte in adultes_district:
                data.append([adulte.nom, adulte.prenom, adulte.profession, adulte.date_de_naissance.strftime("%Y-%m-%d"), adulte.role_dans_leglise, adulte.contact, adulte.baptiser, adulte.status_matrimoniale, adulte.sexe])

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
            return response 
    
    context = {
        'adultes_district': adultes_district,
        'adultes_district_nombre': adultes_district_nombre,
        'eglise': eglise
    }
    return render(request, 'Adultes/adultes_district.html', context)
 
    
def FilteAdultesRegion(request, regs):
    region = get_object_or_404(Region, name=regs)
    adultes_region = Adulte.objects.filter(eglise__region=region)
    adultes_region = filter_by_rbac(request.user, adultes_region, 'adulte')
    adultes_region_nombre = adultes_region.count()
    
    context = {
        'adultes_region' : adultes_region,
        'adultes_region_nombre':adultes_region_nombre,
        'region' : region,
        'regs':regs
    }
    return render(request, 'Adultes/adultes_region.html', context)


def FilteAdultesGroupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    adultes_groupe = Adulte.objects.filter(eglise__groupe=groupe)
    adultes_groupe = filter_by_rbac(request.user, adultes_groupe, 'adulte')
    adultes_groupe_nombre = adultes_groupe.count()
    
    context = {
        'adultes_groupe': adultes_groupe,
        'adultes_groupe_nombre': adultes_groupe_nombre,
        'group': group,
        'groupe':groupe
         
    }
    return render(request, 'Adultes/adultes_groupe.html', context)    


def SearchAdultes(request):
    if request.method == 'POST':
        search_adulte = request.POST['search_adulte']
        search_adultes = Adulte.objects.filter(nom__contains=search_adulte)
        search_adulte_count = search_adultes.count()
        
        context = {
            'search_adulte':search_adulte,
            'search_adultes':search_adultes,
            'search_adulte_count':search_adulte_count,
        }
        return render(request, 'Adultes/search_adultes.html', context)





    
