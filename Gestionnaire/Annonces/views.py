from django.shortcuts import render, redirect, get_object_or_404
from .models import Annonce, Message 
from .forms import AnnoncesForm, MessageForm
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from Eglises.models import Eglise, Region, Groupe



''' ***************  message section    *************** '''

def AddMessage(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save() 
            return redirect('message_details', id=message.id)
        
    else:
        form = MessageForm()
            
    return render(request, 'messages/add_message.html', {'form':form})


def messageList(request):
    messages = Message.objects.all()
    message_count = messages.count()
    
    context = {
        'messages':messages,
        'message_count':message_count
    }
    return render(request, 'messages/messages.html', context)


def messageDetails(request, id):
    message = get_object_or_404(Message, pk=id)
    return render(request, 'messages/message_details.html', {'message':message})


class EditMessage(UpdateView):
    model = Message
    form_class = MessageForm
    context_object_name = 'message'
    template_name = 'messages/edit_messages.html'

class DeleteMessage(DeleteView):
    model = Message
    template_name = 'messages/delete_messages.html'  
    context_object_name = 'message'
    success_url = reverse_lazy('messages')  




''' ***************  search eglise    *************** '''

def SearchEglise(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        search_eglises = Eglise.objects.filter(nom__icontains=searched)
        search_eglise_count = search_eglises.count()
        
        context={
            'searched':searched,
            'search_eglises':search_eglises,
            'search_eglise_count':search_eglise_count
        }
        
        return render(request, 'Eglises/search_eglise.html', context) 
    else:
        return render(request, 'Eglises/search_eglise.html', {})  
    

''' ***************  annonces section    *************** '''

class AnnoncesList(ListView):
    model = Annonce
    template_name = 'Annonces/annonces_list.html'
    paginate_by = 4
    
    
    def get_context_data(self, *args, **kwargs):
        District_list = Eglise.objects.all()
        Groupe_list = Groupe.objects.all()
        Region_list = Region.objects.all()
        nombre_annonces = Annonce.objects.all().count()
        context = super(AnnoncesList, self).get_context_data(*args, **kwargs)
        context["District_list"] = District_list
        context["Groupe_list"] = Groupe_list
        context["Region_list"] = Region_list
        context["nombre_annonces"] = nombre_annonces
        return context
    
    
class AddAnnonces(CreateView):
    model = Annonce
    form_class = AnnoncesForm
    template_name = 'Annonces/add_annonces.html'


class EditAnnonces(UpdateView):
    model = Annonce
    form_class = AnnoncesForm
    context_object_name = 'annonce'
    template_name = 'Annonces/edit_annonces.html'

class DeleteAnnonces(DeleteView):
    model = Annonce
    template_name = 'Annonces/delete_annonces.html'  
    context_object_name = 'annonce'
    success_url = reverse_lazy('annonces_list')  








