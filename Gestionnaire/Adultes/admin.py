from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Adulte
from .resources import AdulteResources



class AdulteAdmin(ImportExportModelAdmin):
    resource_class = AdulteResources

admin.site.register(Adulte, AdulteAdmin)



