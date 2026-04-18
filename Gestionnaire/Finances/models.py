from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from Eglises.models import Eglise

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('ENTREE', 'Entrée (Recette)'),
        ('SORTIE', 'Sortie (Dépense)'),
    )
    
    titre = models.CharField(max_length=200, help_text="Ex: Dîmes Janvier 2026, Achat Matériel")
    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, null=True, blank=True)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_transaction_display()} - {self.titre} ({self.montant})"

    class Meta:
        ordering = ['-date', '-created_at']


class Versement(models.Model):
    """Versement effectué par une église (avec photo du reçu)."""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='versements')
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    photo_recu = models.ImageField(upload_to='images/versements/', blank=True, null=True)
    description = models.TextField(blank=True)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Versement {self.eglise.nom} — {self.montant} FCFA ({self.date})"
