from django.shortcuts import render, get_object_or_404
from .models import Participant, Etablissement, BillanDeLumiere
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView
from .forms import EtablissementForm, ParticipantFrom, BillanDeLumiereFrom
from django.urls import reverse_lazy
#from Jeunes.resources import BillanDeLumiereResource, ParticipantsResource, EtablissementsResource
from django.http import HttpResponse


class AddParticipants(CreateView):
    model = Participant
    template_name = 'Participant/add_participant.html'
    form_class = ParticipantFrom 


class ParticipantList(ListView): 
    model = Participant
    template_name = 'Participant/participants_list.html'
    
    def get_context_data(self, **kwargs):
        Participant_list = Participant.objects.all()
        Participant_list_count = Participant.objects.all().count()
        context = super().get_context_data(**kwargs)
        context["Participant_list"] = Participant_list
        context["Participant_list_count"] = Participant_list_count
        return context
    
def ParticipantsDetail(request, id):
    participant = get_object_or_404(Participant, pk=id)
    return render(request, 'Participant/participants_detail.html', {'participant':participant}) 

class EditParticipant(UpdateView):
    model = Participant
    template_name = 'Participant/edit_participants.html' 
    form_class = ParticipantFrom 

class DeleteParticipant(DeleteView):
    model = Participant
    template_name = 'Participant/delete_participants.html' 
    success_url = reverse_lazy('participants_list')
   
''' 
def export_participant_data(request):
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        participant_resource = ParticipantsResource()
        dataset = participant_resource.export()
        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
            return response
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
            return response   

    return render(request, 'Participant/participant_export.html')

 '''


class EtsList(ListView): 
    model = Etablissement
    template_name = 'Ecole/Ets_list.html'
    
    def get_context_data(self, *args, **kwargs):
        etablissements = Etablissement.objects.all()
        etablissement_count = etablissements.count()
        context = super(EtsList, self).get_context_data(*args, **kwargs)
        context["etablissements"] = etablissements
        context["etablissement_count"] = etablissement_count
        return context

class AddEtablissement(CreateView):
    model = Etablissement
    template_name = 'Ecole/add_etablisement.html'
    form_class = EtablissementForm 
    
class EditEtablissement(UpdateView):
    model = Etablissement
    template_name = 'Ecole/edit_etablissements.html'
    form_class = EtablissementForm  

class DeleteEtablissement(DeleteView):
    model = Etablissement
    template_name = 'Ecole/delete_etablissements.html' 
    success_url = reverse_lazy('etablissements_list')

class EtsDetails(DetailView):
    model = Etablissement
    template_name = 'Ecole/ets_details.html'



class BillanDeLumiereList(ListView):
    model = BillanDeLumiere
    template_name = 'Lumiere/lumieres_list.html'
    
    def get_context_data(self, *args, **kwargs):
        lumieres_list = BillanDeLumiere.objects.all()
        lumieres_list_count = lumieres_list.count()
        context = super(BillanDeLumiereList, self).get_context_data(*args, **kwargs)
        context["lumieres_list"] = lumieres_list
        context["lumieres_list_count"] = lumieres_list_count
        return context

class AddBillanDeLumiere(CreateView):
    model = BillanDeLumiere
    template_name = 'Lumiere/add_lumieres.html'
    form_class = BillanDeLumiereFrom 
    
class EditBillanDeLumiere(UpdateView):
    model = BillanDeLumiere
    template_name = 'Lumiere/edit_lumieres.html'
    form_class = BillanDeLumiereFrom 
    context_object_name = 'lumiere' 
 
class DeleteBillanDeLumiere(DeleteView):
    model = BillanDeLumiere
    template_name = 'Lumiere/delete_lumieres.html' 
    success_url = reverse_lazy('lumieres_list')
    context_object_name = 'lumiere'

def BillanDeLumiereDetail(request, id):
    lumiere = get_object_or_404(BillanDeLumiere, pk=id)
    return render(request, 'Lumiere/lumieres_detail.html', {'lumiere':lumiere}) 

def BillanDeLumiereFilterEts(request, ets):
    etablissements = Etablissement.objects.all()
    bilanLumiere_ets = BillanDeLumiere.objects.filter(etablissements=ets)
    billanLumiere_count = bilanLumiere_ets.count()  
    
    context = {
        'ets':ets,
        'etablissements':etablissements,
        'bilanLumiere_ets':bilanLumiere_ets,
        'billanLumiere_count':billanLumiere_count,
    }
    return render(request, 'Lumiere/lumieres_filtre.html', context)
''' 
def export_lumiere_data(request):
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        lumierebilan_resource = BillanDeLumiereResource()
        dataset = lumierebilan_resource.export()
        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
            return response
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
            return response   

    return render(request, 'Lumiere/lumieres_export.html')

 '''



    