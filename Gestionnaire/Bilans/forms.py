from django import forms
from django.forms import fields
from .models import Cellules, EvenementSpecial, Section



choice = Section.objects.all().values_list('nom', 'nom')



class CellulesForm(forms.ModelForm):
    class Meta:
        model = Cellules
        fields = ('titre', 'district', 'section', 'billan_de_la_cellule', 'date', 'auteur')

        widgets = {
            
            'titre' : forms.TextInput(attrs={'class':'form-control'}),
            'district' : forms.Select(attrs={'class':'form-control'}),
            'section' : forms.Select(choices=choice, attrs={'class':'form-control'}),
            'billan_de_la_cellule' : forms.Textarea(attrs={'class':'form-control'}),
            'date' : forms.DateInput(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'id':'user_id', 'placeholder':'username', 'value':'', 'type':'hidden'}),
            
        }



class EvenementSpecialForm(forms.ModelForm):
    class Meta:
        model = EvenementSpecial
        fields = ('titre', 'type_d_evenement', 'emplacement', 'district', 'billan_de_l_evenement', 'date', 'auteur')

        widgets = {
            
            'titre' : forms.TextInput(attrs={'class':'form-control'}),
            'type_d_evenement' : forms.TextInput(attrs={'class':'form-control'}),
            'emplacement' : forms.TextInput(attrs={'class':'form-control'}),
            'district' : forms.Select(attrs={'class':'form-control'}),
            'billan_de_l_evenement' : forms.Textarea(attrs={'class':'form-control'}),
            'date' : forms.DateInput(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'id':'user_id', 'placeholder':'username', 'type':'hidden'}),
            
        }



