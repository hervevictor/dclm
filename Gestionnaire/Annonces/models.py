from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.urls import reverse


class Annonce(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    image = models.ImageField(blank=True, null=True, upload_to='images/annonces')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    add_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.titre
    
    def get_absolute_url(self):
        return reverse("annonces_list")
    class Meta:
        ordering = ['-add_date'] 
    


class Message(models.Model):
    titre = models.CharField(max_length=200, blank=True, null=True,)
    message = models.FileField(blank=True, null=True, upload_to='messages')
    hymnes = models.CharField(max_length=200, blank=True, null=True,)
    date = models.DateField()
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    add_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.titre} | {self.date} '
    
    def get_absolute_url(self):
        return reverse("message_details", args={str(self.pk)})
    
    class Meta:
        ordering = ['-add_date'] 


 

