from django import forms
from .models import BilanGCK, BilanConferenceMinistres, BilanImpact
from Eglises.models import Eglise


def _eglise_queryset(user):
    """Retourne le queryset d'églises selon le profil RBAC de l'utilisateur."""
    if user is None or user.is_superuser:
        return Eglise.objects.all()
    if not hasattr(user, 'profile'):
        return Eglise.objects.none()
    profil = user.profile
    if profil.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return Eglise.objects.all()
    elif profil.niveau_acces == 'REGION' and profil.region_assignee:
        return Eglise.objects.filter(region__icontains=profil.region_assignee)
    elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
        return Eglise.objects.filter(groupe__icontains=profil.groupe_assigne)
    elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
        return Eglise.objects.filter(nom__icontains=profil.district_assigne)
    return Eglise.objects.none()


class BilanGCKForm(forms.ModelForm):
    class Meta:
        model = BilanGCK
        fields = ('eglise', 'date',
                  'adultes_hommes', 'adultes_femmes',
                  'jeunes_hommes', 'jeunes_femmes',
                  'enfants', 'nouveaux_convertis',
                  'suggestions', 'difficultes', 'auteur')
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-control select-search'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'adultes_hommes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'adultes_femmes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'jeunes_hommes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'jeunes_femmes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'enfants': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nouveaux_convertis': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'suggestions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
            'difficultes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'id': 'current_user', 'type': 'hidden'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['eglise'].queryset = _eglise_queryset(user).order_by('nom')

    def clean(self):
        cleaned_data = super().clean()
        eglise = cleaned_data.get('eglise')
        date = cleaned_data.get('date')

        if eglise and date:
            qs = BilanGCK.objects.filter(eglise=eglise, date=date)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Un bilan GCK existe déjà pour « {eglise.nom} » "
                    f"le {date.strftime('%d/%m/%Y')}. "
                    "Impossible d'enregistrer un doublon."
                )
        return cleaned_data


def _section_form_class(model_class, label_date="Date"):
    """Fabrique un ModelForm générique pour Conference ou Impact."""
    _widgets = {
        'eglise': forms.Select(attrs={'class': 'form-control select-search'}),
        'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        'adultes_hommes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'adultes_femmes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'jeunes_hommes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'jeunes_femmes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'enfants': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'nouveaux_convertis': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'suggestions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
        'difficultes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
        'auteur': forms.TextInput(attrs={'class': 'form-control', 'id': 'current_user', 'type': 'hidden'}),
    }

    class _Form(forms.ModelForm):
        class Meta:
            model = model_class
            fields = ('eglise', 'date',
                      'adultes_hommes', 'adultes_femmes',
                      'jeunes_hommes', 'jeunes_femmes',
                      'enfants', 'nouveaux_convertis',
                      'suggestions', 'difficultes', 'auteur')
            widgets = _widgets

        def __init__(self, *args, user=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['eglise'].queryset = _eglise_queryset(user).order_by('nom')

        def clean(self):
            cleaned_data = super().clean()
            eglise = cleaned_data.get('eglise')
            date = cleaned_data.get('date')
            if eglise and date:
                qs = model_class.objects.filter(eglise=eglise, date=date)
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise forms.ValidationError(
                        f"Un bilan existe déjà pour « {eglise.nom} » "
                        f"le {date.strftime('%d/%m/%Y')}."
                    )
            return cleaned_data

    return _Form


BilanConferenceMinistresForm = _section_form_class(BilanConferenceMinistres)
BilanImpactForm = _section_form_class(BilanImpact)
