from django.contrib import admin
from .models import Jeune

@admin.register(Jeune)
class JeuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'eglise', 'role_dans_leglise', 'telephone', 'created')
    list_filter = ('eglise', 'sexe', 'baptiser')
    search_fields = ('nom', 'prenom', 'telephone')
