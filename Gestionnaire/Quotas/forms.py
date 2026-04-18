from django import forms
from datetime import date
from .models import QuotaRegion, QuotaGroupe, QuotaEglise, VersementQuota
from Eglises.models import Eglise, Region, Groupe


class QuotaRegionForm(forms.ModelForm):
    class Meta:
        model = QuotaRegion
        fields = ['region', 'montant', 'annee']
        widgets = {
            'region': forms.TextInput(attrs={'class': 'form-control', 'list': 'regions-list'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'annee': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('annee') and not self.data.get('annee'):
            self.fields['annee'].initial = date.today().year


class QuotaGroupeForm(forms.ModelForm):
    class Meta:
        model = QuotaGroupe
        fields = ['groupe', 'region', 'montant', 'annee']
        widgets = {
            'groupe': forms.TextInput(attrs={'class': 'form-control', 'list': 'groupes-list'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'list': 'regions-list'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'annee': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('annee') and not self.data.get('annee'):
            self.fields['annee'].initial = date.today().year


class QuotaEgliseForm(forms.ModelForm):
    class Meta:
        model = QuotaEglise
        fields = ['eglise', 'montant', 'annee']
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-select select-search'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'annee': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('annee') and not self.data.get('annee'):
            self.fields['annee'].initial = date.today().year


class VersementQuotaForm(forms.ModelForm):
    class Meta:
        model = VersementQuota
        fields = ['eglise', 'montant', 'date', 'photo_recu', 'description']
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-select select-search'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo_recu': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
