from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from Eglises.models import Eglise


class BilanGCK(models.Model):
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='bilans_gck')
    date = models.DateField(help_text="Date de la croisade GCK")

    # Adultes (stockés H + F séparément)
    adultes_hommes = models.PositiveIntegerField(default=0, verbose_name="Adultes Hommes")
    adultes_femmes = models.PositiveIntegerField(default=0, verbose_name="Adultes Femmes")

    # Jeunes (stockés H + F séparément)
    jeunes_hommes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Hommes")
    jeunes_femmes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Femmes")

    # Enfants (total direct)
    enfants = models.PositiveIntegerField(default=0)

    # Convertis
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
    def total_adultes(self):
        return self.adultes_hommes + self.adultes_femmes

    @property
    def total_jeunes(self):
        return self.jeunes_hommes + self.jeunes_femmes

    @property
    def total_participants(self):
        return self.total_adultes + self.total_jeunes + self.enfants

    def get_absolute_url(self):
        return reverse("gck_detail", args=[str(self.pk)])


class BilanConferenceMinistres(models.Model):
    """Séances du matin lors des GCK — Conférence des Ministres (à partir du 2e jour)"""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='bilans_conference')
    date = models.DateField(help_text="Date de la conférence (matin GCK)")

    adultes_hommes = models.PositiveIntegerField(default=0, verbose_name="Adultes Hommes")
    adultes_femmes = models.PositiveIntegerField(default=0, verbose_name="Adultes Femmes")
    jeunes_hommes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Hommes")
    jeunes_femmes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Femmes")
    enfants = models.PositiveIntegerField(default=0)
    nouveaux_convertis = models.PositiveIntegerField(default=0)
    suggestions = models.TextField(blank=True)
    difficultes = models.TextField(blank=True)

    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bilan Conférence des Ministres"
        verbose_name_plural = "Bilans Conférence des Ministres"
        ordering = ['-date']
        unique_together = ('eglise', 'date')

    def __str__(self):
        return f"Conférence – {self.eglise.nom} – {self.date}"

    @property
    def total_adultes(self):
        return self.adultes_hommes + self.adultes_femmes

    @property
    def total_jeunes(self):
        return self.jeunes_hommes + self.jeunes_femmes

    @property
    def total_participants(self):
        return self.total_adultes + self.total_jeunes + self.enfants

    def get_absolute_url(self):
        return reverse("conference_detail", args=[str(self.pk)])


class BilanImpact(models.Model):
    """Académie d'Impact — chaque samedi matin des GCK (jeunes et jeunes professionnels)"""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='bilans_impact')
    date = models.DateField(help_text="Date du samedi Impact (GCK)")

    adultes_hommes = models.PositiveIntegerField(default=0, verbose_name="Adultes Hommes")
    adultes_femmes = models.PositiveIntegerField(default=0, verbose_name="Adultes Femmes")
    jeunes_hommes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Hommes")
    jeunes_femmes = models.PositiveIntegerField(default=0, verbose_name="Jeunes Femmes")
    enfants = models.PositiveIntegerField(default=0)
    nouveaux_convertis = models.PositiveIntegerField(default=0)
    suggestions = models.TextField(blank=True)
    difficultes = models.TextField(blank=True)

    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bilan Académie d'Impact"
        verbose_name_plural = "Bilans Académie d'Impact"
        ordering = ['-date']
        unique_together = ('eglise', 'date')

    def __str__(self):
        return f"Impact – {self.eglise.nom} – {self.date}"

    @property
    def total_adultes(self):
        return self.adultes_hommes + self.adultes_femmes

    @property
    def total_jeunes(self):
        return self.jeunes_hommes + self.jeunes_femmes

    @property
    def total_participants(self):
        return self.total_adultes + self.total_jeunes + self.enfants

    def get_absolute_url(self):
        return reverse("impact_detail", args=[str(self.pk)])
