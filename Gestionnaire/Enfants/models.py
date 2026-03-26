from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from Eglises.models import Eglise, Region
from ckeditor.fields import RichTextField



class Enfant(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    
    date_de_naissance = models.DateField(max_length=150, auto_now_add=False)
    lieu_de_naissance = models.CharField(max_length=150, blank=True)
     
    classe = models.CharField(max_length=150) 
    sexe = models.CharField(max_length=150)
    
    groupe_sanguin = models.CharField(max_length=25, blank=True)
    rhesus = models.CharField(max_length=10, blank=True)
    talents_de_l_enfant =models.CharField(max_length=400, blank=True)
    avec_qui_vit_il = models.CharField(max_length=100, blank=True)
    nombre_de_freres = models.IntegerField(blank=True)
    les_freres_sont_ils_dans_leglise = models.CharField(max_length=100, blank=True)
    nom_des_freres = models.CharField(max_length=500, blank=True, null=True)
    nombre_de_soeurs = models.IntegerField(blank=True)
    les_soeurs_sont_elles_dans_leglise = models.CharField(max_length=100, blank=True)
    nom_des_soeurs = models.CharField(max_length=500, blank=True, null=True) 
    nom_des_parentes = models.CharField(max_length=400, blank=True) 
    les_parents_sont_ils_dans_leglise = models.CharField(max_length=100, blank=True) 
    
    nom_des_parents_ou_tuteurs = models.CharField(max_length=150, blank=True)
    contact = models.CharField(max_length=150, blank=True)
    description_sur_l_enfant = models.TextField(blank=True)
    enfant_image = models.ImageField(blank=True, null=True, upload_to='images/enfants')
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    
    def get_absolute_url(self):
        return reverse("enfant_details", args={str(self.pk)})
    

