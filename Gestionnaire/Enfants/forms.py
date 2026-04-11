from django import forms
from .models import Enfant
from Eglises.models import Eglise
from Supports.models import Sexe, Reponses

sexs_choice = Sexe.objects.all().values_list('name', 'name')
reponse = Reponses.objects.all().values_list('name', 'name')



class EnfantForm(forms.ModelForm):
    class Meta:
        model = Enfant
        fields = ('nom', 'prenom', 'eglise', 'date_de_naissance', 
                  'lieu_de_naissance', 'classe', 'sexe', 'groupe_sanguin', 
                  'rhesus', 'avec_qui_vit_il', 'nombre_de_freres', 
                  'les_freres_sont_ils_dans_leglise', 'nom_des_freres', 
                  'nombre_de_soeurs', 'les_soeurs_sont_elles_dans_leglise', 
                  'nom_des_soeurs', 'nom_des_parentes', 'les_parents_sont_ils_dans_leglise', 
                  'nom_des_parents_ou_tuteurs', 'contact', 'description_sur_l_enfant', 'enfant_image', 'auteur')
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom' : forms.TextInput(attrs={'class': 'form-control'}),
            'eglise' : forms.Select(attrs={'class': 'form-control select-search'}),            
            'date_de_naissance' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'lieu_de_naissance' : forms.TextInput(attrs={'class': 'form-control'}),
            'classe' : forms.TextInput(attrs={'class': 'form-control'}),
            'sexe' : forms.Select(choices=sexs_choice, attrs={'class': 'form-control'}),
            
            'groupe_sanguin' : forms.TextInput(attrs={'class': 'form-control'}),
            'rhesus' : forms.TextInput(attrs={'class': 'form-control'}),
            'avec_qui_vit_il' : forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_de_freres' : forms.NumberInput(attrs={'class': 'form-control'}),
            'les_freres_sont_ils_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'nom_des_freres' : forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_de_soeurs' : forms.NumberInput(attrs={'class': 'form-control'}),
            'les_soeurs_sont_elles_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'nom_des_soeurs' : forms.TextInput(attrs={'class': 'form-control'}),
            'nom_des_parentes' : forms.TextInput(attrs={'class': 'form-control'}),
            'les_parents_sont_ils_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            
            'nom_des_parents_ou_tuteurs' : forms.TextInput(attrs={'class': 'form-control'}),
            'contact' : forms.NumberInput(attrs={'class': 'form-control'}),
            'enfant_image' : forms.FileInput(attrs={'class': 'form-control'}),
            'description_sur_l_enfant': forms.Textarea(attrs={'class': 'form-control'}),
            
            'auteur': forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'current_user', 'value':'', 'type':'hidden'}),
        }      
        