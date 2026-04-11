from django.contrib import admin
from .models import Retraite, JourRetraite


class JourRetraiteInline(admin.TabularInline):
    model = JourRetraite
    extra = 1
    fields = ('date', 'adultes_h', 'adultes_f', 'jeunes_h', 'jeunes_f',
              'enfants', 'nouveaux_convertis', 'notes_jour')
    ordering = ('date',)


@admin.register(Retraite)
class RetraiteAdmin(admin.ModelAdmin):
    list_display = ('type_retraite', 'region', 'annee', 'nb_jours',
                    'nombre_eglises', 'auteur')
    list_filter = ('type_retraite', 'annee', 'region')
    search_fields = ('region__name', 'lieu', 'theme')
    readonly_fields = ('auteur', 'created', 'updated')
    date_hierarchy = 'date_debut'
    inlines = [JourRetraiteInline]

    fieldsets = (
        ('Identification', {
            'fields': ('type_retraite', 'region', 'annee',
                       'date_debut', 'date_fin', 'lieu', 'theme'),
        }),
        ('Informations', {
            'fields': ('nombre_eglises', 'notes'),
        }),
        ('Méta', {
            'fields': ('auteur', 'created', 'updated'),
            'classes': ('collapse',),
        }),
    )


@admin.register(JourRetraite)
class JourRetraiteAdmin(admin.ModelAdmin):
    list_display = ('retraite', 'date', 'total_participants', 'nouveaux_convertis', 'auteur')
    list_filter = ('retraite__type_retraite', 'retraite__annee', 'retraite__region')
    search_fields = ('retraite__region__name',)
    readonly_fields = ('auteur',)
