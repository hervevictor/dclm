from django.core import paginator
from django.shortcuts import render, get_object_or_404
from .models import Cellules, EvenementSpecial, Section
from .forms import CellulesForm, EvenementSpecialForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from Eglises.models import Eglise, Groupe, Region 
from django.core.paginator import Paginator


class CellulesList(ListView):
    model = Cellules
    template_name = 'Cellules/cellules_list.html'
    paginate_by = 20
    
    def get_context_data(self, *args, **kwargs):
        District_list = Eglise.objects.all()
        Groupe_list = Groupe.objects.all()
        Region_list = Region.objects.all()
        nombre_cellules = Cellules.objects.all().count()
        context = super(CellulesList, self).get_context_data(*args, **kwargs)
        context["District_list"] = District_list
        context["Groupe_list"] = Groupe_list
        context["Region_list"] = Region_list
        context['nombre_cellules'] = nombre_cellules
        return context
    
class AddCellules(CreateView):
    model = Cellules
    form_class = CellulesForm
    template_name = 'Cellules/add_cellules.html'
 
def CellulesDetaill(request, id):
    cellule = get_object_or_404(Cellules, pk=id) 
    Region_list = Region.objects.all()
    return render(request, 'Cellules/cellules_detail.html', {'cellule':cellule, 'Region_list':Region_list})     

class EditCellules(UpdateView):
    model = Cellules
    form_class = CellulesForm
    context_object_name = 'cellule'
    template_name = 'Cellules/edite_cellules.html'
     
class DeleteCellules(DeleteView):
    model = Cellules
    context_object_name = 'cellule'
    template_name = 'Cellules/delete_cellules.html'
    success_url = reverse_lazy('cellules_list')


def FilterCellulesDistricts(request, dist):
    District_list = Districts.objects.all()
    Cellules_districts = Cellules.objects.filter(district=dist) 
    Cellules_districts_count = Cellules.objects.filter(district=dist).count()
    return render(request, 'Cellules/cellules_districts.html', {'dist':dist, 'District_list':District_list, 'Cellules_districts':Cellules_districts, 'Cellules_districts_count':Cellules_districts_count})


def FilterCellulesGroups(request, group):
    Groups_list = Groups.objects.all()
    Cellules_groups = Cellules.objects.filter(groupe=group) 
    Cellules_groups_count = Cellules.objects.filter(groupe=group).count()
    return render(request, 'Cellules/cellules_groups.html', {'group':group, 'Cellules_groups':Cellules_groups, 'Cellules_groups_count':Cellules_groups_count, 'Groups_list':Groups_list})

def FilterCellulesRegion(request, regs):
    Region_list = Region.objects.all()
    Cellules_region = Cellules.objects.filter(region=regs) 
    Cellules_region_count = Cellules.objects.filter(region=regs).count()
    return render(request, 'Cellules/cellules_region.html', {'regs':regs, 'Cellules_region':Cellules_region, 'Cellules_region_count':Cellules_region_count, 'Region_list':Region_list})


def CellulesSection(request, sect):
    Section_list = Section.objects.all()
    Cellules_section = Cellules.objects.filter(section=sect)
    Cellules_section_count = Cellules.objects.filter(section=sect).count()
    return render(request, 'Cellules/cellules_section.html' ,{'sect':sect, 'Section_list':Section_list, 'Cellules_section':Cellules_section, 'Cellules_section_count':Cellules_section_count}) 



''' Section des evenements '''


class EvenementsList(ListView):
    model = EvenementSpecial
    template_name = 'Evenements/evenements_list.html'
    paginate_by = 20
    
    def get_context_data(self, *args, **kwargs):
        District_list = Eglise.objects.all()
        Groupe_list = Groupe.objects.all()
        Region_list = Region.objects.all()
        nombre_evenements = EvenementSpecial.objects.all().count()
        context = super(EvenementsList, self).get_context_data(*args, **kwargs)
        context["District_list"] = District_list
        context["Groupe_list"] = Groupe_list
        context["Region_list"] = Region_list
        context['nombre_evenements'] = nombre_evenements
        return context
    
class AddEvenements(CreateView):
    model = EvenementSpecial
    form_class = EvenementSpecialForm
    template_name = 'Evenements/add_evenements.html'
 
def EvenementsDetail(request, id):
    evenement = get_object_or_404(EvenementSpecial, pk=id) 
    Region_list = Region.objects.all()
    return render(request, 'Evenements/evenements_detail.html', {'evenement':evenement, 'Region_list':Region_list})     

class EditEvenements(UpdateView):
    model = EvenementSpecial
    form_class = EvenementSpecialForm
    template_name = 'Evenements/edite_evenements.html'
     
class DeleteEvenements(DeleteView):
    model = EvenementSpecial
    context_object_name = 'evenement'
    template_name = 'Evenements/delete_evenements.html'
    success_url = reverse_lazy('evenements_list')







