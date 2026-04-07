from django.contrib import admin
from .models import Eglise, Groupe, Region

@admin.register(Eglise)
class EgliseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'groupe', 'ville', 'auteur')
    list_filter = ('region', 'groupe')
    search_fields = ('nom', 'ville')

@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'nom_du_pasteur_du_groupe')
    list_filter = ('region',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'nom_du_pasteur_regional')


