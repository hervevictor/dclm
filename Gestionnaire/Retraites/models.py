from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from Eglises.models import Region


TYPE_RETRAITE = [
    ('DECEMBRE', 'Retraite de Décembre'),
    ('PAQUES', 'Retraite de Pâques'),
]


class Retraite(models.Model):
    type_retraite = models.CharField(
        max_length=20, choices=TYPE_RETRAITE, verbose_name="Type de retraite")
    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, related_name='retraites',
        verbose_name="Région")
    annee = models.PositiveIntegerField(verbose_name="Année")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    lieu = models.CharField(max_length=200, blank=True, verbose_name="Lieu")
    theme = models.CharField(max_length=300, blank=True, verbose_name="Thème")
    nombre_eglises = models.PositiveIntegerField(
        default=0, verbose_name="Nb. d'églises représentées",
        help_text="Nombre total de districts/églises ayant participé")
    notes = models.TextField(blank=True, verbose_name="Observations générales")
    auteur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='retraites_saisies')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-annee', 'type_retraite', 'region__name']
        verbose_name = "Retraite"
        verbose_name_plural = "Retraites"
        unique_together = [('type_retraite', 'region', 'annee')]

    def __str__(self):
        return f"{self.get_type_retraite_display()} {self.annee} — {self.region.name}"

    def get_absolute_url(self):
        return reverse('retraite_detail', args=[self.pk])

    @property
    def nb_jours(self):
        if self.date_fin and self.date_debut:
            return (self.date_fin - self.date_debut).days + 1
        return 1

    # ── Agrégats depuis les rapports journaliers ──────────────────────────────
    @property
    def adultes_h(self):
        return sum(j.adultes_h for j in self.jours.all())

    @property
    def adultes_f(self):
        return sum(j.adultes_f for j in self.jours.all())

    @property
    def total_adultes(self):
        return self.adultes_h + self.adultes_f

    @property
    def jeunes_h(self):
        return sum(j.jeunes_h for j in self.jours.all())

    @property
    def jeunes_f(self):
        return sum(j.jeunes_f for j in self.jours.all())

    @property
    def total_jeunes(self):
        return self.jeunes_h + self.jeunes_f

    @property
    def enfants(self):
        return sum(j.enfants for j in self.jours.all())

    @property
    def nouveaux_convertis(self):
        return sum(j.nouveaux_convertis for j in self.jours.all())

    @property
    def total_participants(self):
        return self.total_adultes + self.total_jeunes + self.enfants


class JourRetraite(models.Model):
    retraite = models.ForeignKey(
        Retraite, on_delete=models.CASCADE, related_name='jours',
        verbose_name="Retraite")
    date = models.DateField(verbose_name="Date du jour")

    adultes_h = models.PositiveIntegerField(default=0, verbose_name="Adultes (H)")
    adultes_f = models.PositiveIntegerField(default=0, verbose_name="Adultes (F)")
    jeunes_h = models.PositiveIntegerField(default=0, verbose_name="Jeunes (H)")
    jeunes_f = models.PositiveIntegerField(default=0, verbose_name="Jeunes (F)")
    enfants = models.PositiveIntegerField(default=0, verbose_name="Enfants")
    nouveaux_convertis = models.PositiveIntegerField(
        default=0, verbose_name="Nouveaux convertis")
    notes_jour = models.TextField(blank=True, verbose_name="Observations du jour")
    auteur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_jours_retraite')

    class Meta:
        ordering = ['date']
        unique_together = [('retraite', 'date')]
        verbose_name = "Rapport journalier"
        verbose_name_plural = "Rapports journaliers"

    def __str__(self):
        return f"{self.retraite} — {self.date}"

    @property
    def total_adultes(self):
        return self.adultes_h + self.adultes_f

    @property
    def total_jeunes(self):
        return self.jeunes_h + self.jeunes_f

    @property
    def total_participants(self):
        return self.total_adultes + self.total_jeunes + self.enfants

    @property
    def numero_jour(self):
        """Numéro du jour dans la retraite (Jour 1, Jour 2…)"""
        if self.retraite.date_debut:
            return (self.date - self.retraite.date_debut).days + 1
        return 1
