from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
from django.contrib.auth.models import User
from Eglises.models import Eglise


class Section(models.Model):
    nom = models.CharField(max_length=200)
    
    def __str__(self):
        return self.nom

class Cellules(models.Model):
    titre = models.CharField(max_length=200)
    district = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    section = models.CharField(max_length=100)
    billan_de_la_cellule = models.TextField()
    date = models.DateField(auto_now_add=False)
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.titre
    
    def get_absolute_url(self):
        return reverse("cellules_list")
    
    



class EvenementSpecial(models.Model):
    titre = models.CharField(max_length=200)
    type_d_evenement = models.CharField(max_length=100)
    emplacement = models.CharField(max_length=100)
    district = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    billan_de_l_evenement = models.TextField()
    date = models.DateField(auto_now_add=False)
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.titre
    
    def get_absolute_url(self):
        return reverse("evenements_detail", args={str(self.pk)})





