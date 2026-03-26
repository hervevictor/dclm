from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone 


class Groupe(models.Model):
    name = models.CharField(max_length=100)
    nom_du_pasteur_du_groupe = models.CharField(max_length=200)
    nom_du_superviseur_des_jeunes = models.CharField(max_length=100)
    nom_du_superviseur_adjoin_des_jeunes = models.CharField(max_length=100)
    nombre_de_membres = models.CharField(max_length=100)
    region = models.CharField(max_length=100) 
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name 
    
    def get_absolute_url(self):
        return reverse("groupe_details", args={str(self.pk)})


class Region(models.Model):
    name = models.CharField(max_length=100)
    nom_du_pasteur_regional = models.CharField(max_length=200)
    nombre_de_membres = models.CharField(max_length=100)
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name 
    
    def get_absolute_url(self):
        return reverse("regions")

 
class Eglise(models.Model):
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    nom_du_pasteur = models.CharField(max_length=100, blank=True)
    nom_du_pasteur_adjoin = models.CharField(max_length=100, blank=True)
    nom_du_dirigeant_des_jeunes = models.CharField(max_length=100, blank=True)
    nom_du_dirigeant_adjoin_des_jeunes = models.CharField(max_length=100, blank=True)
    nom_du_dirigeant_des_enfants = models.CharField(max_length=100, blank=True)
    nom_du_dirigeant_adjoin_des_enfants = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100)
    groupe = models.CharField(max_length=100)
    ville = models.CharField(max_length=250, blank=True)
    nombre_de_membres = models.IntegerField(blank=True, null=True)
    telephone = models.IntegerField(blank=True, null=True)
    bp = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    header_image = models.ImageField(blank=True, null=True, upload_to='images/header')
    body_image = models.ImageField(blank=True, null=True, upload_to='images/Body')
    body_image1 = models.ImageField(blank=True, null=True, upload_to='images/Body')
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nom
    
    def get_absolute_url(self):
        return reverse("eglise_details", args={str(self.pk)})


