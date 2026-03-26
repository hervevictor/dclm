from django.shortcuts import render
from .models import Project, Difficulte
from Eglises.models import Eglise, Groupe, Region
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .forms import ProjectsForm, DifficultesForm
from django.urls import reverse_lazy




class AddProjects(CreateView):
    model = Project
    form_class = ProjectsForm
    template_name = 'Projects/add_projects.html' 

class ProjectsList(ListView):
    model = Project
    template_name = 'Projects/projects_list.html' 
    paginate_by = 20
    
    def get_context_data(self, *args, **kwargs):
        district_list = Eglise.objects.all()
        projects_nombre = Project.objects.all().count()
        context = super(ProjectsList, self).get_context_data(*args, **kwargs)
        context["district_list"] = district_list
        context["projects_nombre"] = projects_nombre
        return context

def ProjectsDetail(request, id):
    Projects_detail = Project.objects.filter(pk=id)
    return render(request, 'Projects/projects_detail.html', {'Projects_detail':Projects_detail, 'Groupe_list':Groupe_list, 'Region_list':Region_list})  

class EditProjects(UpdateView):
    model = Project
    form_class = ProjectsForm
    template_name = 'Projects/edite_projects.html' 

class DeleteProjects(DeleteView):
    model = Project
    form_class = ProjectsForm
    template_name = 'Projects/delete_projects.html' 
    success_url = reverse_lazy('projects_list') 


def FilterProjectsDistricts(request, dist):
    District_list = Eglise.objects.all()
    Projects_districts = Project.objects.filter(district=dist) 
    Projects_districts_count = Projects_districts.count()
    return render(request, 'Projects/projects_districts.html', {'dist':dist, 'District_list':District_list, 'Projects_districts':Projects_districts, 'Projects_districts_count':Projects_districts_count})


def FilterProjectsGroups(request, group):
    Groupe_list = Groupe.objects.all()
    Projects_groups = Project.objects.filter(district=group) 
    Projects_groups_count = Projects_groups.count()
    return render(request, 'Projects/projects_groups.html', {'group':group, 'Projects_groups':Projects_groups, 'Projects_groups_count':Projects_groups_count, 'Groupe_list':Groupe_list})

def FilterProjectsRegion(request, regs):
    Projects_region = Project.objects.filter(region_du_concerne=regs) 
    Projects_region_count = Projects_region.count()
    return render(request, 'Projects/projects_region.html', {'regs':regs, 'Projects_region':Projects_region, 'Projects_region_count':Projects_region_count, 'Region_list':Region_list})





class AddDifficultes(CreateView):
    model = Difficulte
    form_class = DifficultesForm
    template_name = 'Difficultes/add_dfficultes.html' 

class DifficultesList(ListView):
    model = Difficulte
    template_name = 'Difficultes/difficultes_list.html' 
    paginate_by = 20
    
    def get_context_data(self, *args, **kwargs):
        district_list = Eglise.objects.all()
        difficulte_nombre = Difficulte.objects.all().count()
        context = super(DifficultesList, self).get_context_data(*args, **kwargs)
        context["district_list"] = district_list
        context["difficulte_nombre"] = difficulte_nombre
        return context

def DifficultesDetail(request, id):
    Difficultes_detail = Difficulte.objects.filter(pk=id)
    return render(request, 'Difficultes/dfficultes_detail.html', {'Difficultes_detail':Difficultes_detail, 'Groups_list':Groups_list, 'Region_list':Region_list})  

class EditDifficultes(UpdateView):
    model = Difficulte
    form_class = DifficultesForm
    template_name = 'Difficultes/edite_difficultes.html' 

class DeleteDifficultes(DeleteView):
    model = Difficulte
    form_class = DifficultesForm
    template_name = 'Difficultes/delete_difficultes.html' 
    success_url = reverse_lazy('difficultes_list') 


def FilterDifficultesDistricts(request, dist):
    district_list = Eglise.objects.all()
    difficultes_districts = Difficulte.objects.filter(district_du_concerne=dist) 
    difficultes_districts_count = district_list.count()
    return render(request, 'Difficultes/difficultes_districts.html', {'dist':dist, 'district_list':district_list, 'difficultes_districts':difficultes_districts, 'difficultes_districts_count':difficultes_districts_count})


def FilterDifficultesGroups(request, group):
    groupe_list = Groupe.objects.all()
    difficultes_groups = Difficulte.objects.filter(groupe_du_concerne=group) 
    difficultes_groups_count = difficultes_groups.count()
    return render(request, 'Difficultes/difficultes_groups.html', {'group':group, 'difficultes_groups':difficultes_groups, 'difficultes_groups_count':difficultes_groups_count, 'groupe_list':groupe_list})

def FilterDifficultesRegion(request, regs):
    region_list = Region.objects.all()
    difficultes_region = Difficulte.objects.filter(region_du_concerne=regs) 
    difficultes_region_count = difficultes_region.count()
    return render(request, 'Difficultes/difficultes_region.html', {'regs':regs, 'difficultes_region':difficultes_region, 'difficultes_region_count':difficultes_region_count, 'Region_list':Region_list})







