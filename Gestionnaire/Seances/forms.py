from django import forms
from .models import Seance, Bilan
from Eglises.models import Eglise


class BilanForm(forms.ModelForm):
    class Meta:
        model = Bilan
        fields = ('eglise', 'seance', 'adultes_hommes', 'adultes_femmes', 'jeunes_garcons',
                  'jeunes_filles', 'enfants_garcons', 'enfants_filles', 'cotisation', 'date', 'auteur')
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-control select-search'}),
            'seance': forms.Select(attrs={'class': 'form-control'}),
            'adultes_hommes': forms.NumberInput(attrs={'class': 'form-control'}),
            'adultes_femmes': forms.NumberInput(attrs={'class': 'form-control'}),
            'jeunes_garcons': forms.NumberInput(attrs={'class': 'form-control'}),
            'jeunes_filles': forms.NumberInput(attrs={'class': 'form-control'}),
            'enfants_garcons': forms.NumberInput(attrs={'class': 'form-control'}),
            'enfants_filles': forms.NumberInput(attrs={'class': 'form-control'}),
            'cotisation': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'id': 'current_user', 'type': 'hidden'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Restreindre les églises selon le profil RBAC
        if user is None or user.is_superuser:
            qs = Eglise.objects.all()
        elif not hasattr(user, 'profile'):
            qs = Eglise.objects.none()
        else:
            profil = user.profile
            if profil.niveau_acces in ['ADMIN', 'COMPTABLE']:
                qs = Eglise.objects.all()
            elif profil.niveau_acces == 'REGION' and profil.region_assignee:
                qs = Eglise.objects.filter(region__icontains=profil.region_assignee)
            elif profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
                qs = Eglise.objects.filter(groupe__icontains=profil.groupe_assigne)
            elif profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
                qs = Eglise.objects.filter(nom__icontains=profil.district_assigne)
            else:
                qs = Eglise.objects.none()

        self.fields['eglise'].queryset = qs.order_by('nom')

    def clean(self):
        cleaned_data = super().clean()
        eglise = cleaned_data.get('eglise')
        seance = cleaned_data.get('seance')
        date = cleaned_data.get('date')

        if eglise and seance and date:
            # Exclure l'instance en cours de modification
            qs = Bilan.objects.filter(eglise=eglise, seance=seance, date=date)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Un bilan existe déjà pour « {eglise.nom} » "
                    f"({seance}) le {date.strftime('%d/%m/%Y')}. "
                    "Impossible d'enregistrer un doublon."
                )
        return cleaned_data


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
