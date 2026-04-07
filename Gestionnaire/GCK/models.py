from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from Eglises.models import Eglise


class BilanGCK(models.Model):
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='bilans_gck')
    date = models.DateField(help_text="Date de la croisade GCK")

    # Participations
    hommes = models.PositiveIntegerField(default=0)
    femmes = models.PositiveIntegerField(default=0)
    enfants = models.PositiveIntegerField(default=0)
    nouveaux_convertis = models.PositiveIntegerField(default=0)

    # Facultatifs
    suggestions = models.TextField(blank=True)
    difficultes = models.TextField(blank=True)

    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bilan GCK"
        verbose_name_plural = "Bilans GCK"
        ordering = ['-date']
        unique_together = ('eglise', 'date')

    def __str__(self):
        return f"GCK – {self.eglise.nom} – {self.date}"

    @property
    def total_participants(self):
        return self.hommes + self.femmes + self.enfants

    def get_absolute_url(self):
        return reverse("gck_detail", args=[str(self.pk)])
