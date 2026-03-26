from django.db import models
from django.contrib.auth.models import User
from Eglises.models import Eglise, Groupe, Region 
from django.urls import reverse


class Seance(models.Model):
    type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.type}"

class Bilan(models.Model):
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE)
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE)
    adultes_hommes = models.IntegerField(default=0)
    adultes_femmes = models.IntegerField(default=0)
    jeunes_garcons = models.IntegerField(default=0)
    jeunes_filles = models.IntegerField(default=0)
    enfants_garcons = models.IntegerField(default=0)
    enfants_filles = models.IntegerField(default=0)
    cotisation = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField() 
    add_date = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.eglise.name} - {self.seance.type} - {self.seance.date}"
    
    def get_absolute_url(self):
        return reverse("seance_details", args={str(self.pk)}) 
    
    class Meta:
        ordering = ['-add_date'] 
    
    @property
    def total_hommes(self):
        return self.adultes_hommes + self.jeunes_garcons + self.enfants_garcons

    @property
    def total_femmes(self):
        return self.adultes_femmes + self.jeunes_filles + self.enfants_filles

    @property
    def total_assistance(self):
        return (self.adultes_hommes + self.adultes_femmes +
                self.jeunes_garcons + self.jeunes_filles +
                self.enfants_garcons + self.enfants_filles)





