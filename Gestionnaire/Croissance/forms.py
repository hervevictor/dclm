from django import forms
from .models import NouveauVenu


class NouveauVenuForm(forms.ModelForm):
    class Meta:
        model = NouveauVenu
        fields = ['eglise', 'nom', 'prenom', 'sexe', 'categorie',
                  'telephone', 'adresse', 'date_venue', 'origine', 'statut', 'observations']
        widgets = {
            'eglise':       forms.Select(attrs={'class': 'form-select select-search'}),
            'nom':          forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':       forms.TextInput(attrs={'class': 'form-control'}),
            'sexe':         forms.Select(attrs={'class': 'form-select'}),
            'categorie':    forms.Select(attrs={'class': 'form-select'}),
            'telephone':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 90000000'}),
            'adresse':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quartier, ville…'}),
            'date_venue':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'origine':      forms.Select(attrs={'class': 'form-select'}),
            'statut':       forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class FiltreNouveauVenuForm(forms.Form):
    FILTRE_CHOICES = [
        ('mois', 'Par mois'),
        ('annee', 'Par année'),
        ('periode', 'Par intervalle de dates'),
    ]
    mode        = forms.ChoiceField(choices=FILTRE_CHOICES, required=False,
                                    widget=forms.Select(attrs={'class': 'form-select form-select-sm', 'id': 'mode-filtre'}))
    mois        = forms.DateField(required=False,
                                  widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'month'}))
    annee       = forms.IntegerField(required=False, min_value=2000, max_value=2100,
                                     widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 2025'}))
    date_debut  = forms.DateField(required=False,
                                  widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}))
    date_fin    = forms.DateField(required=False,
                                  widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}))
    origine     = forms.ChoiceField(required=False,
                                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    statut      = forms.ChoiceField(required=False,
                                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    categorie   = forms.ChoiceField(required=False,
                                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import NouveauVenu
        self.fields['origine'].choices = [('', 'Toutes origines')] + list(NouveauVenu.ORIGINE_CHOICES)
        self.fields['statut'].choices  = [('', 'Tous statuts')]   + list(NouveauVenu.STATUT_CHOICES)
        self.fields['categorie'].choices = [('', 'Toutes catégories')] + list(NouveauVenu.CATEGORIE_CHOICES)
