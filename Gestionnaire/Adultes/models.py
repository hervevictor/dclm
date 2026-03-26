from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from Eglises.models import Eglise
from ckeditor.fields import RichTextField



class Adulte(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    
    date_de_naissance = models.DateField(max_length=150, auto_now_add=False)
    lieu_de_naissance = models.CharField(max_length=150)
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE)
        
    profession = models.CharField(max_length=150) 
    sexe = models.CharField(max_length=150)
    status_matrimoniale = models.CharField(max_length=150, blank=True)
    
    groupe_sanguin = models.CharField(max_length=25, blank=True)
    rhesus = models.CharField(max_length=10, blank=True)
    role_dans_leglise = models.CharField(max_length=70, blank=True)

    contact = models.CharField(max_length=150, blank=True)
    contact_whatsapp = models.CharField(max_length=150, blank=True, null=True)
    annee_de_conversion = models.CharField(max_length=150, blank=True)
    baptiser = models.CharField(max_length=150, blank=True)
    annee_de_bapteme = models.CharField(max_length=150, blank=True)
    nombre_d_enfant = models.CharField(max_length=150, blank=True)
    description_sur_vous_et_votre_famille = models.TextField(blank=True)
    adulte_image = models.ImageField(blank=True, null=True, upload_to='images/adulte')
    
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    
    def get_absolute_url(self):
        return reverse("adulte_details", args={str(self.pk)})
    


