from django import forms
from .models import Adulte
from Eglises.models import Eglise
from Supports.models import Sexe, Reponses, Ocupation, Roles


profession = Ocupation.objects.all().values_list('name', 'name')
role = Roles.objects.all().values_list('name', 'name')
sexs_choice = Sexe.objects.all().values_list('name', 'name')
reponse = Reponses.objects.all().values_list('name', 'name')





#Adultes section
class AdulteForm(forms.ModelForm):
    class Meta:
        model = Adulte
        fields = ('nom', 'prenom', 'date_de_naissance', 'lieu_de_naissance',
                  'eglise', 'profession', 'sexe', 'status_matrimoniale', 
                  'groupe_sanguin', 'rhesus', 'role_dans_leglise', 
                  'contact', 'contact_whatsapp', 'annee_de_conversion', 'baptiser', 
                  'annee_de_bapteme', 'nombre_d_enfant', 'description_sur_vous_et_votre_famille', 
                  'adulte_image', 'auteur')
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom' : forms.TextInput(attrs={'class': 'form-control'}),
            'eglise' : forms.Select(attrs={'class': 'form-control select-search'}),
                        
            'date_de_naissance' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'lieu_de_naissance' : forms.TextInput(attrs={'class': 'form-control'}),
            'profession' : forms.Select(choices=profession, attrs={'class': 'form-control'}),
            'sexe' : forms.Select(choices=sexs_choice, attrs={'class': 'form-control'}),
            
            'groupe_sanguin' : forms.TextInput(attrs={'class': 'form-control'}),
            'rhesus' : forms.TextInput(attrs={'class': 'form-control'}),
            'role_dans_leglise' : forms.Select(choices=role, attrs={'class': 'form-control'}),
            
            'status_matrimoniale' : forms.TextInput(attrs={'class': 'form-control'}),
            'contact' : forms.TextInput(attrs={'class': 'form-control'}),
            'contact_whatsapp' : forms.TextInput(attrs={'class': 'form-control'}),
            'annee_de_conversion' : forms.TextInput(attrs={'class': 'form-control'}),
            'baptiser' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'annee_de_bapteme' : forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_d_enfant' : forms.TextInput(attrs={'class': 'form-control'}),
            
            'description_sur_vous_et_votre_famille' : forms.Textarea(attrs={'class': 'form-control'}),
            'adulte_image' : forms.FileInput(attrs={'class': 'form-control'}),
            
            'auteur': forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'current_user', 'value':'', 'type':'hidden'}),

        }
        
        
 