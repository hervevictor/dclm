from django.contrib import admin
from .models import BilanGCK, BilanConferenceMinistres, BilanImpact

_DISPLAY = ('eglise', 'date', 'adultes_hommes', 'adultes_femmes',
            'jeunes_hommes', 'jeunes_femmes', 'enfants',
            'nouveaux_convertis', 'total_participants', 'auteur')
_FILTERS = ('date', 'eglise__region', 'eglise__groupe')
_SEARCH = ('eglise__nom', 'eglise__region', 'eglise__groupe')


@admin.register(BilanGCK)
class BilanGCKAdmin(admin.ModelAdmin):
    list_display = _DISPLAY
    list_filter = _FILTERS
    search_fields = _SEARCH
    date_hierarchy = 'date'


@admin.register(BilanConferenceMinistres)
class BilanConferenceAdmin(admin.ModelAdmin):
    list_display = _DISPLAY
    list_filter = _FILTERS
    search_fields = _SEARCH
    date_hierarchy = 'date'


@admin.register(BilanImpact)
class BilanImpactAdmin(admin.ModelAdmin):
    list_display = _DISPLAY
    list_filter = _FILTERS
    search_fields = _SEARCH
    date_hierarchy = 'date'
