from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm 
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile
from Eglises.models import Region, Groupe, Eglise



class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    
    class Meta:
        model = User 
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')
        
    
     
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        if commit:
            user.save()
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user, defaults={'niveau_acces': 'DISTRICT'})
        return user
    



class EditUserForm(UserChangeForm):
    """Formulaire de modification du profil personnel — champs sensibles exclus."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class PasswordChangingForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))
    new_password1 = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))
    new_password2 = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('niveau_acces', 'section_assignee', 'region_assignee', 'groupe_assigne', 'district_assigne')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        
        try:
            region_choices = [('', '---------')] + [(r.name, r.name) for r in Region.objects.all()]
            groupe_choices = [('', '---------')] + [(g.name, g.name) for g in Groupe.objects.all()]
            district_choices = [('', '---------')] + [(e.nom, e.nom) for e in Eglise.objects.all()]
        except Exception:
            region_choices, groupe_choices, district_choices = [], [], []

        self.fields['region_assignee'] = forms.ChoiceField(
            choices=region_choices, required=False, label="Région assignée",
            widget=forms.Select(attrs={'class': 'form-select select-search'})
        )
        self.fields['groupe_assigne'] = forms.ChoiceField(
            choices=groupe_choices, required=False, label="Groupe assigné",
            widget=forms.Select(attrs={'class': 'form-select select-search'})
        )
        self.fields['district_assigne'] = forms.ChoiceField(
            choices=district_choices, required=False, label="District assigné",
            widget=forms.Select(attrs={'class': 'form-select select-search'})
        )
