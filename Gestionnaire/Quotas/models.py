from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from Eglises.models import Eglise

GRAND_LOME = 'Grand Lomé'


def annee_courante():
    return date.today().year


class QuotaRegion(models.Model):
    """Quota attribué par le siège à une région (sauf Grand Lomé)."""
    region = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    annee = models.IntegerField(default=annee_courante)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_attribution = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('region', 'annee')
        ordering = ['region']

    def __str__(self):
        return f"{self.region} – {self.annee} – {self.montant} FCFA"


class QuotaGroupe(models.Model):
    """Quota attribué par la région à un groupe."""
    groupe = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    annee = models.IntegerField(default=annee_courante)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_attribution = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('groupe', 'annee')
        ordering = ['region', 'groupe']

    def __str__(self):
        return f"{self.groupe} – {self.annee} – {self.montant} FCFA"


class QuotaEglise(models.Model):
    """Quota attribué par le groupe à une église."""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='quotas')
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    annee = models.IntegerField(default=annee_courante)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotas_eglise')
    date_attribution = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('eglise', 'annee')
        ordering = ['eglise__groupe', 'eglise__nom']

    def __str__(self):
        return f"{self.eglise.nom} – {self.annee} – {self.montant} FCFA"


class VersementQuota(models.Model):
    """Paiement d'une église vers son quota (distinct des cotisations de culte)."""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='versements_quota')
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    photo_recu = models.ImageField(upload_to='images/quotas/', blank=True, null=True)
    description = models.TextField(blank=True)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='versements_quota')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.eglise.nom} – {self.date} – {self.montant} FCFA"
