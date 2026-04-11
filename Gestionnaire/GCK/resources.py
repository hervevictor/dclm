from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import BilanGCK, BilanConferenceMinistres, BilanImpact
from Eglises.models import Eglise


class BilanGCKResource(resources.ModelResource):
    eglise = fields.Field(column_name='Église', attribute='eglise', widget=ForeignKeyWidget(Eglise, 'nom'))
    groupe = fields.Field(column_name='Groupe')
    region = fields.Field(column_name='Région')
    total_adultes = fields.Field(column_name='Total Adultes')
    total_jeunes = fields.Field(column_name='Total Jeunes')
    total_general = fields.Field(column_name='Total Général')

    class Meta:
        model = BilanGCK
        fields = ('date', 'eglise', 'groupe', 'region',
                  'adultes_hommes', 'adultes_femmes', 'total_adultes',
                  'jeunes_hommes', 'jeunes_femmes', 'total_jeunes',
                  'enfants', 'total_general', 'nouveaux_convertis')
        export_order = ('date', 'eglise', 'groupe', 'region',
                        'adultes_hommes', 'adultes_femmes', 'total_adultes',
                        'jeunes_hommes', 'jeunes_femmes', 'total_jeunes',
                        'enfants', 'total_general', 'nouveaux_convertis')

    def dehydrate_groupe(self, bilan):
        return bilan.eglise.groupe

    def dehydrate_region(self, bilan):
        return bilan.eglise.region

    def dehydrate_total_adultes(self, bilan):
        return bilan.total_adultes

    def dehydrate_total_jeunes(self, bilan):
        return bilan.total_jeunes

    def dehydrate_total_general(self, bilan):
        return bilan.total_participants


def _make_resource(model_class):
    """Fabrique une ressource tablib identique pour Conference et Impact."""
    class _Resource(resources.ModelResource):
        eglise = fields.Field(column_name='Église', attribute='eglise', widget=ForeignKeyWidget(Eglise, 'nom'))
        groupe = fields.Field(column_name='Groupe')
        region = fields.Field(column_name='Région')
        total_adultes = fields.Field(column_name='Total Adultes')
        total_jeunes = fields.Field(column_name='Total Jeunes')
        total_general = fields.Field(column_name='Total Général')

        class Meta:
            model = model_class
            fields = ('date', 'eglise', 'groupe', 'region',
                      'adultes_hommes', 'adultes_femmes', 'total_adultes',
                      'jeunes_hommes', 'jeunes_femmes', 'total_jeunes',
                      'enfants', 'total_general', 'nouveaux_convertis')
            export_order = fields

        def dehydrate_groupe(self, bilan): return bilan.eglise.groupe
        def dehydrate_region(self, bilan): return bilan.eglise.region
        def dehydrate_total_adultes(self, bilan): return bilan.total_adultes
        def dehydrate_total_jeunes(self, bilan): return bilan.total_jeunes
        def dehydrate_total_general(self, bilan): return bilan.total_participants

    return _Resource


BilanConferenceMinistresResource = _make_resource(BilanConferenceMinistres)
BilanImpactResource = _make_resource(BilanImpact)
