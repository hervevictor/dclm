from django import forms
from .models import Seance, Bilan 


class BilanForm(forms.ModelForm):
    class Meta:
        model = Bilan 
        fields = ('eglise', 'seance', 'adultes_hommes', 'adultes_femmes', 'jeunes_garcons', 
                  'jeunes_filles', 'enfants_garcons', 'enfants_filles', 'cotisation', 'date', 'auteur')
        
        widgets = {
            'eglise':forms.Select(attrs={'class':'form-control'}),
            'seance':forms.Select(attrs={'class':'form-control'}),
            'adultes_hommes':forms.NumberInput(attrs={'class':'form-control'}),
            'adultes_femmes':forms.NumberInput(attrs={'class':'form-control'}),
            'jeunes_garcons':forms.NumberInput(attrs={'class':'form-control'}),
            'jeunes_filles':forms.NumberInput(attrs={'class':'form-control'}),
            'enfants_garcons':forms.NumberInput(attrs={'class':'form-control'}),
            'enfants_filles':forms.NumberInput(attrs={'class':'form-control'}),
            'cotisation':forms.NumberInput(attrs={'class':'form-control'}),
            'date':forms.DateInput(attrs={'class':'form-control', 'type':'date'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'placeholder':'username', 'id':'current_user', 'value':'', 'type':'hidden'}),
        }



class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class':'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class':'form-control'}), required=False)


