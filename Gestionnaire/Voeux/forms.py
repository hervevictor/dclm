from django import forms
from .models import (TypeContribution, Voeu, VersementVoeu, Contribution,
                     VersementContribution, HistoriqueVoeu, HistoriqueContribution)
from Eglises.models import Eglise
from Adultes.models import Adulte

_DATE_WIDGET = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
_NUM_WIDGET = forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
_TEXT_WIDGET = forms.TextInput(attrs={'class': 'form-control'})
_TEXTAREA_WIDGET = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
_SELECT_WIDGET = forms.Select(attrs={'class': 'form-select select-search'})


def _eglise_qs(user):
    if user is None or user.is_superuser:
        return Eglise.objects.all()
    if not hasattr(user, 'profile'):
        return Eglise.objects.none()
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return Eglise.objects.all()
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return Eglise.objects.filter(region__icontains=p.region_assignee)
    if p.niveau_acces == 'GROUPE' and p.groupe_assigne:
        return Eglise.objects.filter(groupe__icontains=p.groupe_assigne)
    if p.niveau_acces == 'DISTRICT' and p.district_assigne:
        return Eglise.objects.filter(nom__icontains=p.district_assigne)
    return Eglise.objects.none()


def _membre_qs(user, eglise_pk=None):
    """Retourne les membres (Adultes) filtrés par église.
    Si aucune église n'est précisée, retourne un queryset vide pour ne jamais
    exposer des membres d'autres districts."""
    if eglise_pk:
        return Adulte.objects.filter(eglise_id=eglise_pk).order_by('nom', 'prenom')
    return Adulte.objects.none()


# ─── VOEU ─────────────────────────────────────────────────────────────────────

class VoeuForm(forms.ModelForm):
    class Meta:
        model = Voeu
        fields = ('eglise', 'membre', 'date_voeu', 'montant_promis',
                  'premier_versement', 'details', 'auteur')
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_eglise'}),
            'membre': forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_membre'}),
            'date_voeu': _DATE_WIDGET,
            'montant_promis': _NUM_WIDGET,
            'premier_versement': _NUM_WIDGET,
            'details': _TEXTAREA_WIDGET,
            'auteur': forms.HiddenInput(attrs={'id': 'current_user'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eglise'].queryset = _eglise_qs(user).order_by('nom')
        # Si une église est déjà sélectionnée (edit ou POST), filtrer les membres
        eglise_pk = None
        if self.data.get('eglise'):
            try:
                eglise_pk = int(self.data['eglise'])
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.eglise_id:
            eglise_pk = self.instance.eglise_id
        self.fields['membre'].queryset = _membre_qs(user, eglise_pk)
        self.fields['premier_versement'].required = False


class VersementVoeuForm(forms.ModelForm):
    class Meta:
        model = VersementVoeu
        fields = ('montant', 'date', 'notes', 'auteur')
        widgets = {
            'montant': _NUM_WIDGET,
            'date': _DATE_WIDGET,
            'notes': _TEXTAREA_WIDGET,
            'auteur': forms.HiddenInput(attrs={'id': 'current_user'}),
        }


# ─── CONTRIBUTION ─────────────────────────────────────────────────────────────

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ('eglise', 'membre', 'type_contribution', 'date_contribution',
                  'montant_objectif', 'details', 'auteur')
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_eglise'}),
            'membre': forms.Select(attrs={'class': 'form-select select-search', 'id': 'id_membre'}),
            'type_contribution': forms.Select(attrs={'class': 'form-select'}),
            'date_contribution': _DATE_WIDGET,
            'montant_objectif': _NUM_WIDGET,
            'details': _TEXTAREA_WIDGET,
            'auteur': forms.HiddenInput(attrs={'id': 'current_user'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eglise'].queryset = _eglise_qs(user).order_by('nom')
        eglise_pk = None
        if self.data.get('eglise'):
            try:
                eglise_pk = int(self.data['eglise'])
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.eglise_id:
            eglise_pk = self.instance.eglise_id
        self.fields['membre'].queryset = _membre_qs(user, eglise_pk)
        self.fields['type_contribution'].queryset = TypeContribution.objects.filter(actif=True)
        self.fields['montant_objectif'].required = False


class VersementContributionForm(forms.ModelForm):
    class Meta:
        model = VersementContribution
        fields = ('montant', 'date', 'notes', 'auteur')
        widgets = {
            'montant': _NUM_WIDGET,
            'date': _DATE_WIDGET,
            'notes': _TEXTAREA_WIDGET,
            'auteur': forms.HiddenInput(attrs={'id': 'current_user'}),
        }


# ─── MODIFICATION DE MONTANT AVEC JUSTIFICATION ───────────────────────────────

class ModifierMontantVoeuForm(forms.Form):
    nouveau_montant = forms.IntegerField(
        min_value=1,
        label="Nouveau montant promis (FCFA)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
    )
    justification = forms.CharField(
        label="Justification de la modification",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': "Expliquez pourquoi ce montant est modifié (erreur de saisie, accord du membre, etc.)",
        }),
    )


class ModifierMontantContributionForm(forms.Form):
    nouveau_montant = forms.IntegerField(
        required=False,
        min_value=1,
        label="Nouveau montant objectif (FCFA)",
        help_text="Laisser vide pour supprimer l'objectif.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
    )
    justification = forms.CharField(
        label="Justification de la modification",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': "Expliquez pourquoi ce montant est modifié.",
        }),
    )


class CorrectionVersementForm(forms.Form):
    nouveau_montant = forms.IntegerField(
        min_value=1,
        label="Montant corrigé (FCFA)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
    )
    justification = forms.CharField(
        label="Justification de la correction",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': "Expliquez la raison de cette correction (erreur de saisie, etc.)",
        }),
    )


# ─── TYPE DE CONTRIBUTION (Admin) ─────────────────────────────────────────────

class TypeContributionForm(forms.ModelForm):
    class Meta:
        model = TypeContribution
        fields = ('nom', 'description', 'actif', 'ordre')
        widgets = {
            'nom': _TEXT_WIDGET,
            'description': _TEXTAREA_WIDGET,
            'ordre': _NUM_WIDGET,
        }
