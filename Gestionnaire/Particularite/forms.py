from django import forms
from .models import Project, Difficulte



class DifficultesForm(forms.ModelForm):
    class Meta:
        model = Difficulte
        fields = ('nom_complet', 'district', 'telephone', 'description')
        
        widgets = {
            'nom_complet' : forms.TextInput(attrs={'class':'form-control'}),
            'district' : forms.Select(attrs={'class':'form-control'}),
            'telephone' : forms.NumberInput(attrs={'class':'form-control'}),
            'description' : forms.Textarea(attrs={'class': 'form-control'}),
        }

class ProjectsForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('nom_complet', 'district', 'telephone', 'description')
        
        widgets = {
            'nom_complet' : forms.TextInput(attrs={'class':'form-control'}),
            'district' : forms.Select(attrs={'class':'form-control'}),
            'telephone' : forms.NumberInput(attrs={'class':'form-control'}),
            'description' : forms.Textarea(attrs={'class':'form-control'}),
        }




