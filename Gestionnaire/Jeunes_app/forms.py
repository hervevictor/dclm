from django import forms
from .models import Jeune
from Eglises.models import Eglise, Region
from Supports.models import Sexe, Reponses, Ocupation, Roles


choice = Ocupation.objects.all().values_list('name', 'name')
role = Roles.objects.all().values_list('name', 'name')
sexs_choice = Sexe.objects.all().values_list('name', 'name')
reponse = Reponses.objects.all().values_list('name', 'name')

reg_choice = Region.objects.all().values_list('name', 'name')





class JeuneForm(forms.ModelForm):
    class Meta:
        model = Jeune
        fields = ('nom', 'prenom', 'eglise', 'telephone', 'date_de_naissance', 
                  'lieu_de_naissance', 'sexe', 'classe_ou_niveau_d_etude', 
                  'Faculte_ou_domaine_d_emploie', 'groupe_sanguin', 'rhesus', 
                  'role_dans_leglise', 'annee_de_conversion', 'baptiser', 'annee_de_bapteme', 'avec_qui_vit_il', 
                  'nombre_de_freres', 'les_freres_sont_ils_dans_leglise', 
                  'nom_des_freres', 'nombre_de_soeurs', 'les_soeurs_sont_elles_dans_leglise', 
                  'nom_des_soeurs', 'nom_des_parents', 'les_parents_sont_ils_dans_leglise', 
                  'numero_de_telephone_des_parents_ou_tuteurs', 
                  'jeune_image', 'description', 'auteur')
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom' : forms.TextInput(attrs={'class': 'form-control'}),
            'eglise' : forms.Select(attrs={'class': 'form-control select-search'}),
            'telephone': forms.NumberInput(attrs={'class': 'form-control'}),
             
            'date_de_naissance' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'lieu_de_naissance' : forms.TextInput(attrs={'class': 'form-control'}),
            'sexe' : forms.Select(choices=sexs_choice, attrs={'class': 'form-control'}),
            'groupe_sanguin' : forms.TextInput(attrs={'class': 'form-control'}),
            'rhesus' : forms.TextInput(attrs={'class': 'form-control'}),
            'role_dans_leglise' : forms.Select(choices=role, attrs={'class': 'form-control'}),
            
            'numero_de_telephone_du_jeune' : forms.NumberInput(attrs={'class': 'form-control'}),
            'annee_de_conversion' : forms.TextInput(attrs={'class': 'form-control'}),
            'baptiser' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'annee_de_bapteme' : forms.TextInput(attrs={'class': 'form-control'}),
            'avec_qui_vit_il' : forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_de_freres' : forms.NumberInput(attrs={'class': 'form-control'}),
            'les_freres_sont_ils_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'nom_des_freres' : forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_de_soeurs' : forms.NumberInput(attrs={'class': 'form-control'}),
            'les_soeurs_sont_elles_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'nom_des_soeurs' : forms.TextInput(attrs={'class': 'form-control'}),
            'nom_des_parents' : forms.TextInput(attrs={'class': 'form-control'}),
            'les_parents_sont_ils_dans_leglise' : forms.Select(choices=reponse, attrs={'class': 'form-control'}),
            'numero_de_telephone_des_parents_ou_tuteurs' : forms.NumberInput(attrs={'class': 'form-control'}),
            'classe_ou_niveau_d_etude' : forms.TextInput(attrs={'class': 'form-control'}), 
            'Faculte_ou_domaine_d_emploie' : forms.TextInput(attrs={'class': 'form-control'}),          
            
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'jeune_image' : forms.FileInput(attrs={'class': 'form-control'}),
            
            'auteur': forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'current_user', 'value':'', 'type':'hidden'}),
        }
