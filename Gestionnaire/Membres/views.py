from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm  , UserChangeForm, PasswordChangeForm 
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .forms import RegisterForm, EditUserForm, PasswordChangingForm
from django.contrib.auth.views import PasswordChangeView



class UserRegister(CreateView):
    form_class  = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    

class UserEditeProfile(UpdateView):
    form_class = EditUserForm
    template_name = 'registration/edit_compte.html' 
    success_url = reverse_lazy('login')
    
    def get_object(self):
        return self.request.user


def password_success(request):
    return render(request, 'registration/password_success.html', {})


class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('password_success')

