from django.contrib import admin
from .models import BilanGCK


@admin.register(BilanGCK)
class BilanGCKAdmin(admin.ModelAdmin):
    list_display = ('eglise', 'date', 'hommes', 'femmes', 'enfants', 'nouveaux_convertis', 'total_participants', 'auteur')
    list_filter = ('date', 'eglise__region', 'eglise__groupe')
    search_fields = ('eglise__nom', 'eglise__region', 'eglise__groupe')
    date_hierarchy = 'date'
