from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse
from Eglises.models import Eglise
from Adultes.models import Adulte


class TypeContribution(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Type de Contribution"
        verbose_name_plural = "Types de Contribution"

    def __str__(self):
        return self.nom


# ─── VOEUX ────────────────────────────────────────────────────────────────────

class Voeu(models.Model):
    """Voeu (promesse) d'un membre avec montant obligatoire."""
    membre = models.ForeignKey(Adulte, on_delete=models.CASCADE, related_name='voeux',
                               verbose_name="Membre")
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='voeux',
                               verbose_name="Église (District)")
    montant_promis = models.PositiveIntegerField(verbose_name="Montant promis (FCFA)")
    details = models.TextField(blank=True, verbose_name="Détails / Objet du voeu")
    date_voeu = models.DateField(verbose_name="Date du voeu")

    premier_versement = models.PositiveIntegerField(
        default=0, verbose_name="Premier versement (FCFA)",
        help_text="Facultatif — laisser 0 si pas de versement immédiat"
    )

    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='voeux_saisis')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_voeu']
        verbose_name = "Voeu"
        verbose_name_plural = "Voeux"

    def __str__(self):
        return f"Voeu — {self.membre} — {self.montant_promis:,} FCFA"

    def get_absolute_url(self):
        return reverse("voeu_detail", args=[self.pk])

    @property
    def total_paye(self):
        return self.versements.aggregate(s=Sum('montant'))['s'] or 0

    @property
    def montant_restant(self):
        return max(0, self.montant_promis - self.total_paye)

    @property
    def est_solde(self):
        return self.montant_restant == 0

    @property
    def pourcentage(self):
        if self.montant_promis == 0:
            return 100
        return min(100, int(self.total_paye * 100 / self.montant_promis))


class VersementVoeu(models.Model):
    """Paiement partiel ou total d'un voeu."""
    voeu = models.ForeignKey(Voeu, on_delete=models.CASCADE, related_name='versements')
    montant = models.PositiveIntegerField(verbose_name="Montant (FCFA)")
    date = models.DateField(verbose_name="Date du versement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Versement Voeu"
        verbose_name_plural = "Versements Voeux"

    def __str__(self):
        return f"{self.montant:,} FCFA — {self.date}"


class HistoriqueVoeu(models.Model):
    """Trace chaque modification du montant promis d'un voeu."""
    voeu = models.ForeignKey(Voeu, on_delete=models.CASCADE, related_name='historiques')
    ancien_montant = models.PositiveIntegerField(verbose_name="Ancien montant (FCFA)")
    nouveau_montant = models.PositiveIntegerField(verbose_name="Nouveau montant (FCFA)")
    justification = models.TextField(verbose_name="Justification de la modification")
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='historiques_voeux')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "Historique modification Voeu"
        verbose_name_plural = "Historiques modifications Voeux"

    def __str__(self):
        return f"Modification voeu #{self.voeu_id} : {self.ancien_montant:,} → {self.nouveau_montant:,} FCFA"


# ─── CONTRIBUTIONS ────────────────────────────────────────────────────────────

class Contribution(models.Model):
    """Contribution d'un membre (montant cible facultatif)."""
    membre = models.ForeignKey(Adulte, on_delete=models.CASCADE, related_name='contributions',
                               verbose_name="Membre")
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name='contributions',
                               verbose_name="Église (District)")
    type_contribution = models.ForeignKey(TypeContribution, on_delete=models.PROTECT,
                                          related_name='contributions',
                                          verbose_name="Type de contribution")
    montant_objectif = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Montant objectif (FCFA)",
        help_text="Facultatif — si renseigné, le restant sera calculé automatiquement"
    )
    details = models.TextField(blank=True, verbose_name="Détails")
    date_contribution = models.DateField(verbose_name="Date")

    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='contributions_saisies')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_contribution']
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"

    def __str__(self):
        return f"Contribution ({self.type_contribution}) — {self.membre}"

    def get_absolute_url(self):
        return reverse("contribution_detail", args=[self.pk])

    @property
    def total_verse(self):
        return self.versements.aggregate(s=Sum('montant'))['s'] or 0

    @property
    def montant_restant(self):
        if self.montant_objectif:
            return max(0, self.montant_objectif - self.total_verse)
        return None

    @property
    def est_solde(self):
        if self.montant_objectif:
            return self.total_verse >= self.montant_objectif
        return False

    @property
    def pourcentage(self):
        if not self.montant_objectif or self.montant_objectif == 0:
            return None
        return min(100, int(self.total_verse * 100 / self.montant_objectif))


class VersementContribution(models.Model):
    """Paiement vers une contribution."""
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE,
                                     related_name='versements')
    montant = models.PositiveIntegerField(verbose_name="Montant (FCFA)")
    date = models.DateField(verbose_name="Date du versement")
    notes = models.TextField(blank=True)
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Versement Contribution"
        verbose_name_plural = "Versements Contributions"

    def __str__(self):
        return f"{self.montant:,} FCFA — {self.date}"


class HistoriqueContribution(models.Model):
    """Trace chaque modification du montant objectif d'une contribution."""
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE,
                                     related_name='historiques')
    ancien_montant = models.PositiveIntegerField(null=True, blank=True,
                                                  verbose_name="Ancien montant objectif (FCFA)")
    nouveau_montant = models.PositiveIntegerField(null=True, blank=True,
                                                   verbose_name="Nouveau montant objectif (FCFA)")
    justification = models.TextField(verbose_name="Justification de la modification")
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='historiques_contributions')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "Historique modification Contribution"
        verbose_name_plural = "Historiques modifications Contributions"

    def __str__(self):
        return f"Modification contrib #{self.contribution_id} : {self.ancien_montant} → {self.nouveau_montant} FCFA"


# ─── CORRECTIONS DE VERSEMENTS ────────────────────────────────────────────────

class HistoriqueVersementVoeu(models.Model):
    """Trace chaque correction du montant d'un versement de voeu."""
    versement = models.ForeignKey(VersementVoeu, on_delete=models.CASCADE,
                                  related_name='historiques')
    ancien_montant = models.PositiveIntegerField(verbose_name="Ancien montant (FCFA)")
    nouveau_montant = models.PositiveIntegerField(verbose_name="Nouveau montant (FCFA)")
    justification = models.TextField(verbose_name="Justification de la correction")
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='historiques_versements_voeux')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "Historique correction Versement Voeu"
        verbose_name_plural = "Historiques corrections Versements Voeux"

    def __str__(self):
        return f"Correction versement #{self.versement_id} : {self.ancien_montant:,} → {self.nouveau_montant:,} FCFA"


class HistoriqueVersementContribution(models.Model):
    """Trace chaque correction du montant d'un versement de contribution."""
    versement = models.ForeignKey(VersementContribution, on_delete=models.CASCADE,
                                  related_name='historiques')
    ancien_montant = models.PositiveIntegerField(verbose_name="Ancien montant (FCFA)")
    nouveau_montant = models.PositiveIntegerField(verbose_name="Nouveau montant (FCFA)")
    justification = models.TextField(verbose_name="Justification de la correction")
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='historiques_versements_contributions')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "Historique correction Versement Contribution"
        verbose_name_plural = "Historiques corrections Versements Contributions"

    def __str__(self):
        return f"Correction versement #{self.versement_id} : {self.ancien_montant:,} → {self.nouveau_montant:,} FCFA"
