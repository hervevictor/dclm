from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Jeune
from Eglises.models import Eglise, Region, Groupe 
from django.urls import reverse_lazy
from .forms import JeuneForm
from Membres.utils import filter_by_rbac


from Adultes.resources import JeuneResources
from django.http import HttpResponse
from tablib import Dataset
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors



  


''' Jeunes '''


class AddJeune(CreateView):
    model = Jeune 
    form_class = JeuneForm
    template_name = 'Jeunes/add_jeune.html'

class JeuneList(ListView):
    model = Jeune 
    template_name = 'Jeunes/jeune_liste.html'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return filter_by_rbac(self.request.user, qs, 'jeune')
        
    def get_context_data(self, *args, **kwargs):
        context = super(JeuneList, self).get_context_data(*args, **kwargs)
        context["jeunes"] = self.get_queryset().count()
        return context
    
class JeuneDetails(DetailView):
    model = Jeune 
    template_name = 'Jeunes/jeune_details.html'
 
class EditJeune(UpdateView):
    model = Jeune
    form_class = JeuneForm
    template_name = 'Jeunes/edit_jeune.html'   
    
class DeleteJeune(DeleteView):
    model = Jeune 
    template_name = 'Jeunes/delete_jeune.html'
    success_url = reverse_lazy('jeunes')
 
 
     
def FilteJeunesDistrict(request, dist):
    eglise = get_object_or_404(Eglise, pk=dist)
    jeunes_district = Jeune.objects.filter(eglise=dist)
    jeunes_district = filter_by_rbac(request.user, jeunes_district, 'jeune')
    jeunes_district_nombre = jeunes_district.count()
    
    
    resource = JeuneResources()
    
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        dataset = resource.export(jeunes_district)
        
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
            response['Content-Disposition'] = f'attachment; filename="jeunes_district_{eglise.nom}.pdf"'
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Table data
            data = [["Nom", "Prénom", "Classe/Niveau", "Faculte/D Emploie", "Role", "Contact", "Baptiser", "Sexe"]]
            for jeune in jeunes_district:
                data.append([jeune.nom, jeune.prenom, jeune.classe_ou_niveau_d_etude, jeune.Faculte_ou_domaine_d_emploie,jeune.role_dans_leglise, jeune.telephone, jeune.baptiser, jeune.sexe])

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
        'jeunes_district': jeunes_district,
        'jeunes_district_nombre': jeunes_district_nombre,
        'eglise': eglise
    }
    return render(request, 'Jeunes/jeunes_district.html', context)
 
    
def FilteJeunesRegion(request, regs):
    region = get_object_or_404(Region, name=regs)
    jeunes_region = Jeune.objects.filter(eglise__region=region)
    jeunes_region = filter_by_rbac(request.user, jeunes_region, 'jeune')
    jeunes_region_nombre = jeunes_region.count()
    
    context = {
        'jeunes_region' : jeunes_region,
        'jeunes_region_nombre':jeunes_region_nombre,
        'region' : region,
        'regs':regs
    }
    return render(request, 'Jeunes/jeunes_region.html', context)


def FilteJeunesGroupe(request, group):
    groupe = get_object_or_404(Groupe, name=group)
    jeunes_groupe = Jeune.objects.filter(eglise__groupe=groupe)
    jeunes_groupe = filter_by_rbac(request.user, jeunes_groupe, 'jeune')
    jeunes_groupe_nombre = jeunes_groupe.count()
    
    context = {
        'jeunes_groupe': jeunes_groupe,
        'jeunes_groupe_nombre': jeunes_groupe_nombre,
        'group': group,
        'groupe':groupe
         
    }
    return render(request, 'Jeunes/jeunes_groupe.html', context)    

def SearchJeunes(request):
    if request.method == 'POST':
        search_jeune = request.POST['search_jeune']
        search_jeunes = Jeune.objects.filter(nom__contains=search_jeune)
        search_jeune_count = search_jeunes.count()
        
        context = {
            'search_jeune':search_jeune,
            'search_jeunes': search_jeunes,
            'search_jeune_count':search_jeune_count
        }
        return render(request, 'Jeunes/search_jeunes.html', context)



    
