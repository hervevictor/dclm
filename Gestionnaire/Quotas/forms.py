from django import forms
from datetime import date
from .models import QuotaRegion, QuotaGroupe, QuotaEglise, VersementQuota, PromesseQuota, GRAND_LOME
from Eglises.models import Eglise, Region, Groupe
from Adultes.models import Adulte


class QuotaRegionForm(forms.ModelForm):
    class Meta:
        model = QuotaRegion
        fields = ['region', 'montant', 'annee']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'annee': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        regions = Region.objects.exclude(name=GRAND_LOME).order_by('name')
        self.fields['region'] = forms.ChoiceField(
            choices=[('', '— Sélectionner une région —')] + [(r.name, r.name) for r in regions],
            label='Région',
            widget=forms.Select(attrs={'class': 'form-select select-search'}),
        )
        if not self.initial.get('annee') and not self.data.get('annee'):
            self.fields['annee'].initial = date.today().year


class QuotaGroupeForm(forms.ModelForm):
    class Meta:
        model = QuotaGroupe
        fields = ['groupe', 'region', 'montant', 'annee']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant en FCFA'}),
            'annee': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        regions = Region.objects.all().order_by('name')
        groupes = Groupe.objects.all().order_by('name')
        self.fields['region'] = forms.ChoiceField(
            choices=[('', '— Sélectionner une région —')] + [(r.name, r.name) for r in regions],
            label='Région',
            widget=forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_region'}),
        )
        self.fields['groupe'] = forms.ChoiceField(
            choices=[('', '— Sélectionner un groupe —')] + [(g.name, g.name) for g in groupes],
            label='Groupe',
            widget=forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_groupe'}),
        )
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


class PromesseQuotaForm(forms.ModelForm):
    class Meta:
        model = PromesseQuota
        fields = ['nom_membre', 'montant_promis', 'montant_paye', 'statut', 'date', 'notes']
        widgets = {
            'montant_promis': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant promis (FCFA)'}),
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant déjà payé (FCFA)'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, eglise=None, **kwargs):
        super().__init__(*args, **kwargs)
        if eglise:
            membres = Adulte.objects.filter(eglise=eglise).order_by('nom', 'prenom')
            choices = [('', '— Sélectionner un membre —')] + [
                (f"{m.nom} {m.prenom}", f"{m.nom} {m.prenom}") for m in membres
            ]
            self.fields['nom_membre'] = forms.ChoiceField(
                choices=choices,
                label='Membre',
                widget=forms.Select(attrs={'class': 'form-select select-search'}),
            )
        else:
            self.fields['nom_membre'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du membre'})


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
