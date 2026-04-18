from django import forms
from .models import Groupe, Region, Eglise

choice_grp = Groupe.objects.all().values_list('name', 'name')
choice = Region.objects.all().values_list('name', 'name')


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ('name', 'nom_du_pasteur_regional', 'nombre_de_membres')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_pasteur_regional': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_de_membres': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GroupeForm(forms.ModelForm):
    class Meta:
        model = Groupe
        fields = ('name', 'nom_du_pasteur_du_groupe',
                  'nom_du_superviseur_des_jeunes', 'nom_du_superviseur_adjoin_des_jeunes',
                  'region')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_pasteur_du_groupe': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_superviseur_des_jeunes': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_superviseur_adjoin_des_jeunes': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(choices=choice, attrs={'class': 'form-control'}),
        }


class EgliseForm(forms.ModelForm):
    class Meta:
        model = Eglise
        fields = (
            'auteur', 'nom', 'groupe', 'ville', 'region',
            'nom_du_pasteur',
            'nom_du_dirigeant_des_jeunes',
            'nom_du_dirigeant_des_enfants',
            'coordinatrice_des_femmes',
            'dirigeant_de_zone1',
            'dirigeant_de_zone2',
            'responsable_des_femmes1',
            'responsable_des_femmes2',
            'responsable_des_jeunes_femme',
            'responsable_des_jeunes_professionnel',
            'telephone', 'bp', 'email', 'description',
            'header_image', 'body_image', 'body_image1',
        )
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'groupe': forms.Select(choices=choice_grp, attrs={'class': 'form-control'}),
            'region': forms.Select(choices=choice, attrs={'class': 'form-control'}),
            'nom_du_pasteur': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_dirigeant_des_jeunes': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_dirigeant_des_enfants': forms.TextInput(attrs={'class': 'form-control'}),
            'coordinatrice_des_femmes': forms.TextInput(attrs={'class': 'form-control'}),
            'dirigeant_de_zone1': forms.TextInput(attrs={'class': 'form-control'}),
            'dirigeant_de_zone2': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable_des_femmes1': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable_des_femmes2': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable_des_jeunes_femme': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable_des_jeunes_professionnel': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.NumberInput(attrs={'class': 'form-control'}),
            'bp': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username',
                                             'id': 'current_user', 'value': '', 'type': 'hidden'}),
        }
