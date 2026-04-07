from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import BilanGCK
from Eglises.models import Eglise


class BilanGCKResource(resources.ModelResource):
    eglise = fields.Field(column_name='Église', attribute='eglise', widget=ForeignKeyWidget(Eglise, 'nom'))
    groupe = fields.Field(column_name='Groupe')
    region = fields.Field(column_name='Région')

    class Meta:
        model = BilanGCK
        fields = ('date', 'eglise', 'groupe', 'region',
                  'hommes', 'femmes', 'enfants', 'nouveaux_convertis')
        export_order = ('date', 'eglise', 'groupe', 'region',
                        'hommes', 'femmes', 'enfants', 'nouveaux_convertis')

    def dehydrate_groupe(self, bilan):
        return bilan.eglise.groupe

    def dehydrate_region(self, bilan):
        return bilan.eglise.region
