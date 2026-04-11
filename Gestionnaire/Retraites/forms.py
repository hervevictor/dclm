from django import forms
from .models import Retraite, JourRetraite, TYPE_RETRAITE
from Eglises.models import Region
from datetime import date

_NUM = forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
_DATE = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
_TEXT = forms.TextInput(attrs={'class': 'form-control'})
_AREA = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})


def _region_qs(user):
    if user is None or user.is_superuser:
        return Region.objects.all()
    if not hasattr(user, 'profile'):
        return Region.objects.none()
    p = user.profile
    if p.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return Region.objects.all()
    if p.niveau_acces == 'REGION' and p.region_assignee:
        return Region.objects.filter(name__icontains=p.region_assignee)
    return Region.objects.none()


class RetraiteForm(forms.ModelForm):
    class Meta:
        model = Retraite
        fields = (
            'type_retraite', 'region', 'annee', 'date_debut', 'date_fin',
            'lieu', 'theme', 'nombre_eglises', 'notes',
        )
        widgets = {
            'type_retraite': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'date_debut': _DATE,
            'date_fin': _DATE,
            'lieu': _TEXT,
            'theme': _TEXT,
            'nombre_eglises': _NUM,
            'notes': _AREA,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = _region_qs(user).order_by('name')
        self.fields['date_fin'].required = False
        self.fields['lieu'].required = False
        self.fields['theme'].required = False
        self.fields['notes'].required = False
        if not self.instance.pk:
            self.fields['annee'].initial = date.today().year


class JourRetraiteForm(forms.ModelForm):
    class Meta:
        model = JourRetraite
        fields = (
            'date',
            'adultes_h', 'adultes_f',
            'jeunes_h', 'jeunes_f',
            'enfants', 'nouveaux_convertis',
            'notes_jour',
        )
        widgets = {
            'date': _DATE,
            'adultes_h': _NUM,
            'adultes_f': _NUM,
            'jeunes_h': _NUM,
            'jeunes_f': _NUM,
            'enfants': _NUM,
            'nouveaux_convertis': _NUM,
            'notes_jour': _AREA,
        }

    def __init__(self, *args, retraite=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.retraite = retraite
        self.fields['notes_jour'].required = False
        if retraite:
            # Contraindre la date dans la plage de la retraite
            self.fields['date'].widget.attrs['min'] = str(retraite.date_debut)
            if retraite.date_fin:
                self.fields['date'].widget.attrs['max'] = str(retraite.date_fin)

    def clean_date(self):
        d = self.cleaned_data['date']
        if self.retraite:
            if d < self.retraite.date_debut:
                raise forms.ValidationError(
                    f"La date ne peut pas être avant le début de la retraite "
                    f"({self.retraite.date_debut.strftime('%d/%m/%Y')})."
                )
            if self.retraite.date_fin and d > self.retraite.date_fin:
                raise forms.ValidationError(
                    f"La date ne peut pas dépasser la fin de la retraite "
                    f"({self.retraite.date_fin.strftime('%d/%m/%Y')})."
                )
        return d
