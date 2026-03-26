from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from .models import Bilan, Seance, Eglise, Groupe 


class GroupeResource(resources.ModelResource):
    class Meta:
        model = Groupe
        fields = '_all_'


class BilanResource(resources.ModelResource):
    eglise_name = fields.Field(column_name='eglise', attribute='eglise', widget=ForeignKeyWidget(Eglise, 'name'))
    seance_name = fields.Field(column_name='seance', attribute='seance', widget=ForeignKeyWidget(Seance, 'type'))
    date = fields.Field(column_name='date', attribute='date', widget=DateWidget(format='%Y-%m-%d'))

    class Meta:
        model = Bilan
        fields = ('id', 'date', 'eglise_name', 'seance_name', 'adultes_hommes', 'adultes_femmes', 
                  'jeunes_garcons', 'jeunes_filles', 'enfants_garcons', 'enfants_filles', 'cotisation')
        export_order = ('id', 'date', 'eglise_name', 'seance_name', 'adultes_hommes', 'adultes_femmes', 
                        'jeunes_garcons', 'jeunes_filles', 'enfants_garcons', 'enfants_filles', 'cotisation')