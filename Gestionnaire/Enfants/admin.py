from django.contrib import admin
from .models import Enfant

@admin.register(Enfant)
class EnfantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'eglise', 'region', 'classe', 'created')
    list_filter = ('eglise', 'region', 'sexe')
    search_fields = ('nom', 'prenom')
