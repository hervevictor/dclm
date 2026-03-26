from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from ckeditor.fields import RichTextField



class Etablissement(models.Model):
    name = models.CharField(max_length=200)
    groupe_titulaire = models.CharField(max_length=200)
    region = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("etablissements_list")
    
     
class Participant(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=50)
    age = models.CharField(max_length=20)
    numero = models.CharField(max_length=150, null=True, blank=True)
    eglise_frequente = models.CharField(max_length=200)
    classe = models.CharField(max_length=50)
    residence = models.CharField(max_length=150)
    probleme_particulier = models.TextField(null=True, blank=True)
    projets = models.TextField(null=True, blank=True)
    etablissement = models.CharField(max_length=100)
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nom + '  ' + str(self.prenom) 
    
    def get_absolute_url(self):
        return reverse("participant_detail", args={str(self.pk)})
    
    
     

class BillanDeLumiere(models.Model):
    titre = models.CharField(max_length=200)
    etablissements = models.CharField(max_length=100)
    enseignant = models.CharField(max_length=100)
    numbre_de_fille = models.CharField(max_length=100)
    numbre_de_garcon = models.CharField(max_length=100)
    rapports_suggestions = models.TextField()
    date = models.DateField(auto_now_add=False)
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.titre
    
    def get_absolute_url(self):
        return reverse("lumieres_list")
    
    




