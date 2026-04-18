from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from Eglises.models import Eglise


class NouveauVenu(models.Model):

    ORIGINE_CHOICES = [
        ('INVITATION', 'Invitation personnelle'),
        ('GCK', 'Converti GCK (séance du soir)'),
        ('EVANGELISATION', 'Évangélisation'),
        ('SEANCE', 'Première séance (de passage)'),
        ('AUTRE', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('SUIVI', 'En cours de suivi'),
        ('RESTE', "Intégré(e) dans l'église"),
        ('PARTI', 'Parti(e)'),
    ]

    CATEGORIE_CHOICES = [
        ('ADULTE', 'Adulte'),
        ('JEUNE', 'Jeune'),
        ('ENFANT', 'Enfant'),
    ]

    SEXE_CHOICES = [
        ('H', 'Homme / Garçon'),
        ('F', 'Femme / Fille'),
    ]

    eglise      = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='nouveaux_venus')
    nom         = models.CharField(max_length=100)
    prenom      = models.CharField(max_length=100, blank=True)
    sexe        = models.CharField(max_length=1, choices=SEXE_CHOICES)
    categorie   = models.CharField(max_length=10, choices=CATEGORIE_CHOICES, default='ADULTE')
    telephone   = models.CharField(max_length=30, blank=True)
    adresse     = models.CharField(max_length=200, blank=True)
    date_venue  = models.DateField(default=timezone.now)
    origine     = models.CharField(max_length=20, choices=ORIGINE_CHOICES)
    statut      = models.CharField(max_length=10, choices=STATUT_CHOICES, default='SUIVI')
    observations = models.TextField(blank=True)
    auteur      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_venue']

    def __str__(self):
        return f"{self.nom} {self.prenom} – {self.eglise.nom} ({self.date_venue})"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}".strip()
