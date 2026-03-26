from django.db import models
from Eglises.models import Eglise





class Difficulte(models.Model):
    nom_complet = models.CharField(max_length=200)
    district = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    telephone = models.IntegerField(blank=True)
    add_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.nom_complet
    
    def get_absolute_url(self):
        return reverse("difficulte_details", args={str(self.pk)})
     
     

class Project(models.Model):
    nom_complet = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    district = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    telephone = models.IntegerField(blank=True)
    add_date = models.DateField(auto_now_add=True) 
    
    def __str__(self):
        return self.nom_complet
    
    def get_absolute_url(self):
        return reverse("project_details", args={str(self.pk)})   






