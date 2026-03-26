from django import forms
from django.forms import fields, widgets
from .models import Participant, Etablissement, BillanDeLumiere
from Supports.models import Sexe
from Eglises.models import Region, Groupe

choices = Sexe.objects.all().values_list('name' , 'name')
choice = Etablissement.objects.all().values_list('name' , 'name')

reg_choix = Region.objects.all().values_list('name', 'name')
groupe_choix = Groupe.objects.all().values_list('name' , 'name')

choice_list = []
for item in choices:
    choice_list.append(item)


class EtablissementForm(forms.ModelForm):
    class Meta:
        model = Etablissement
        fields = ('name', 'groupe_titulaire', 'region', 'description', 'auteur')  
        
        widgets = {
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'groupe_titulaire' : forms.Select(choices=groupe_choix, attrs={'class':'form-control'}),
            'region' : forms.Select(choices=reg_choix, attrs={'class':'form-control'}),
            'description' : forms.Textarea(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class': 'form-control', 'placeholder':'username', 'id':'ets_user', 'value':'', 'type':'hidden'}),
        }


class ParticipantFrom(forms.ModelForm):
    class Meta:
        model = Participant
        fields =  ('nom', 'prenom', 'sexe', 'age', 'numero', 'eglise_frequente', 'classe', 'residence', 'probleme_particulier', 'projets', 'etablissement', 'auteur') 

        
        widgets = {
            'nom' : forms.TextInput(attrs={'class':'form-control'}),
            'prenom' : forms.TextInput(attrs={'class':'form-control'}),
            'sexe' : forms.Select(choices=choice_list, attrs={'class':'form-control'}),
            'age' : forms.TextInput(attrs={'class':'form-control'}),
            'numero' : forms.TextInput(attrs={'class':'form-control'}),
            'eglise_frequente' : forms.TextInput(attrs={'class':'form-control'}),
            'classe' : forms.TextInput(attrs={'class':'form-control'}),
            'etablissement' : forms.TextInput(attrs={'class':'form-control'}),
            'residence' : forms.TextInput(attrs={'class':'form-control'}),
            'probleme_particulier' : forms.Textarea(attrs={'class':'form-control'}), 
            'projets' : forms.Textarea(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'participant_user', 'value':'', 'type':'hidden'}),
            
        }




class BillanDeLumiereFrom(forms.ModelForm):
    class Meta:
        model = BillanDeLumiere
        fields = ('titre', 'etablissements', 'enseignant', 'numbre_de_fille', 'numbre_de_garcon', 'rapports_suggestions', 'date', 'auteur')

        
        widgets = {
            'titre' : forms.TextInput(attrs={'class':'form-control'}),
            'etablissements' : forms.Select(choices=choice, attrs={'class':'form-control'}),
            'enseignant' : forms.TextInput(attrs={'class':'form-control'}),
            'numbre_de_fille' : forms.TextInput(attrs={'class':'form-control'}),
            'numbre_de_garcon' : forms.TextInput(attrs={'class':'form-control'}),
            'rapports_suggestions' : forms.Textarea(attrs={'class':'form-control'}),
            'date' : forms.TextInput(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'bilan_user', 'value':'', 'type':'hidden'}),
            
        }








