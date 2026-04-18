from django.contrib import admin
from .models import NouveauVenu


@admin.register(NouveauVenu)
class NouveauVenuAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'eglise', 'categorie', 'sexe', 'date_venue', 'origine', 'statut')
    list_filter = ('statut', 'origine', 'categorie', 'sexe', 'eglise__region', 'eglise__groupe')
    search_fields = ('nom', 'prenom', 'telephone', 'eglise__nom')
    date_hierarchy = 'date_venue'
