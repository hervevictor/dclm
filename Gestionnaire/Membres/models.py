from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    NIVEAUX = (
        ('REGION', 'Région (Grand Lomé)'),
        ('GROUPE', 'Groupe'),
        ('DISTRICT', 'District (Église locale)'),
        ('COMPTABLE', 'Secrétaire / Comptable National'),
        ('ADMIN', 'Administrateur Global'),
    )
    niveau_acces = models.CharField(max_length=20, choices=NIVEAUX, default='DISTRICT')
    
    SECTIONS_CHOICES = (
        ('TOUS', 'Toutes les sections (Pasteur/Admin)'),
        ('ADULTES', 'Section Adultes'),
        ('JEUNES', 'Section Jeunes'),
        ('ENFANTS', 'Section Enfants'),
    )
    section_assignee = models.CharField(max_length=20, choices=SECTIONS_CHOICES, default='TOUS', help_text="Restreindre l'accès à une section spécifique au sein de l'église")
    
    region_assignee = models.CharField(max_length=100, blank=True, null=True, help_text="Nom exact de la Région si niveau = REGION")
    groupe_assigne = models.CharField(max_length=100, blank=True, null=True, help_text="Nom exact du Groupe si niveau = GROUPE")
    district_assigne = models.CharField(max_length=100, blank=True, null=True, help_text="Nom exact du District/Église si niveau = DISTRICT")

    def __str__(self):
        return f"Profil de {self.user.username} ({self.get_niveau_acces_display()})"

    def is_admin(self):
        return self.niveau_acces in ['ADMIN', 'COMPTABLE'] or self.user.is_superuser

    def can_access_section(self, section):
        """Vérifie si l'utilisateur a accès à une section donnée (ADULTES, JEUNES, ENFANTS)."""
        return self.section_assignee == 'TOUS' or self.section_assignee == section


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un UserProfile lors de la création d'un utilisateur."""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'niveau_acces': 'DISTRICT'}
        )
