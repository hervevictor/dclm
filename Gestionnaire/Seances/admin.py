from django.contrib import admin
from .models import Seance, Bilan

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ('type',)

@admin.register(Bilan)
class BilanAdmin(admin.ModelAdmin):
    list_display = ('eglise', 'seance', 'date', 'total_assistance', 'cotisation', 'auteur')
    list_filter = ('date', 'seance', 'eglise')
    date_hierarchy = 'date'


