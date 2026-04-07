from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Adulte
from .resources import AdulteResources



class AdulteAdmin(ImportExportModelAdmin):
    resource_class = AdulteResources
    list_display = ('nom', 'prenom', 'eglise', 'role_dans_leglise', 'contact', 'created')
    list_filter = ('eglise', 'sexe', 'baptiser')
    search_fields = ('nom', 'prenom', 'contact')

admin.site.register(Adulte, AdulteAdmin)



