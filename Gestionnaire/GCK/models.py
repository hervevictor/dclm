from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from Eglises.models import Eglise

# Types de séance GCK (créés automatiquement si absents)
_GCK_SEANCE_TYPES = {
    0: 'GCK Lundi soir',
    3: 'GCK Jeudi soir',
    6: 'GCK Dimanche soir',
}


def _get_or_create_seance(type_name):
    from Seances.models import Seance
    obj, _ = Seance.objects.get_or_create(type=type_name)
    return obj


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

    # Quête de la séance GCK
    quete = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Quête (FCFA)")

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

    # ── Synchronisation automatique vers Séances ────────────────────────────
    def _seance_type_name(self):
        return _GCK_SEANCE_TYPES.get(self.date.weekday())

    def _sync_bilan_seance(self):
        """Crée ou met à jour le Bilan de Séances correspondant à ce rapport GCK."""
        from Seances.models import Bilan
        type_name = self._seance_type_name()
        if not type_name:
            return
        seance = _get_or_create_seance(type_name)
        Bilan.objects.update_or_create(
            eglise=self.eglise,
            seance=seance,
            date=self.date,
            defaults={
                'adultes_hommes': self.adultes_hommes,
                'adultes_femmes': self.adultes_femmes,
                'jeunes_garcons': self.jeunes_hommes,
                'jeunes_filles': self.jeunes_femmes,
                'enfants_garcons': self.enfants,
                'enfants_filles': 0,
                'cotisation': self.quete,
                'auteur': self.auteur,
            }
        )

    def _delete_bilan_seance(self):
        """Supprime le Bilan de Séances lié si ce rapport GCK est supprimé."""
        from Seances.models import Bilan, Seance
        type_name = self._seance_type_name()
        if not type_name:
            return
        seance = Seance.objects.filter(type=type_name).first()
        if seance:
            Bilan.objects.filter(eglise=self.eglise, seance=seance, date=self.date).delete()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._sync_bilan_seance()

    def delete(self, *args, **kwargs):
        self._delete_bilan_seance()
        super().delete(*args, **kwargs)


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
