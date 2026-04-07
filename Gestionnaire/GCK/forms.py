from django import forms
from .models import BilanGCK
from Eglises.models import Eglise


class BilanGCKForm(forms.ModelForm):
    class Meta:
        model = BilanGCK
        fields = ('eglise', 'date', 'hommes', 'femmes', 'enfants',
                  'nouveaux_convertis', 'suggestions', 'difficultes', 'auteur')
        widgets = {
            'eglise': forms.Select(attrs={'class': 'form-control select-search'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hommes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'femmes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'enfants': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nouveaux_convertis': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'suggestions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
            'difficultes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Facultatif'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'id': 'current_user', 'type': 'hidden'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Restreindre les choix d'église selon le profil RBAC
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
