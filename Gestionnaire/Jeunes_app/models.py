from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from Eglises.models import Eglise, Region
from ckeditor.fields import RichTextField



class Jeune(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    telephone = models.IntegerField(blank=True)
    
    date_de_naissance = models.DateField(auto_now_add=False, blank=False)
    lieu_de_naissance = models.CharField(max_length=100, blank=True)
    sexe = models.CharField(max_length=100)
    
    groupe_sanguin = models.CharField(max_length=25, blank=True)
    rhesus = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True) 
    role_dans_leglise = models.CharField(max_length=70, blank=True)
    talents_du_jeune =models.CharField(max_length=400, blank=True, null=True)
    avec_qui_vit_il = models.CharField(max_length=100, blank=True, null=True)
    nombre_de_freres = models.IntegerField(blank=True, null=True)
    les_freres_sont_ils_dans_leglise = models.CharField(max_length=100, blank=True, null=True)
    nom_des_freres = models.CharField(max_length=500, blank=True, null=True)
    nombre_de_soeurs = models.IntegerField(blank=True, null=True)
    les_soeurs_sont_elles_dans_leglise = models.CharField(max_length=100, blank=True, null=True)
    nom_des_soeurs = models.CharField(max_length=500, blank=True, null=True) 
    nom_des_parents = models.CharField(max_length=400) 
    les_parents_sont_ils_dans_leglise = models.CharField(max_length=100, blank=True, null=True)
    
    annee_de_conversion = models.CharField(max_length=150, blank=True)
    baptiser = models.CharField(max_length=150, blank=True)
    annee_de_bapteme = models.CharField(max_length=150, blank=True)
     
    numero_de_telephone_des_parents_ou_tuteurs = models.IntegerField(blank=True, null=True)
    classe_ou_niveau_d_etude = models.CharField(max_length=200, blank=True, null=True)
    Faculte_ou_domaine_d_emploie = models.CharField(max_length=200, blank=True, null=True)
    jeune_image = models.ImageField(blank=True, null=True, upload_to='images/jeunes')
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nom} {self.prenom}" 
    
    
    def get_absolute_url(self):
        return reverse("jeune_details", args={str(self.pk)})
    


    

