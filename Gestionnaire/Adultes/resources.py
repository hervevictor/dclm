from import_export import resources
from .models import Adulte
from Enfants.models import Enfant
from Jeunes_app.models import Jeune
from Eglises.models import Eglise


class AdulteResources(resources.ModelResource):
    class Meta:
        model = Adulte 
        fields =  ('nom', 'prenom', 'profession', 'status_matrimoniale', 'role_dans_leglise', 'contact', 'baptiser', 'sexe')



class JeuneResources(resources.ModelResource):
    class Meta:
        model = Jeune 
        fields =  ('nom', 'prenom', 'classe_ou_niveau_d_etude', 'Faculte_ou_domaine_d_emploie', 'role_dans_leglise', 'telephone', 'baptiser', 'sexe')

class EnfantResources(resources.ModelResource):
    class Meta:
        model = Enfant 
        fields =  ('nom', 'prenom', 'classe', 'date_de_naissance', 'lieu_de_naissance', 'contact', 'sexe')



class EgliseResources(resources.ModelResource):
    class Meta:
        model = Eglise 
        fields =  ('nom', 'nom_du_pasteur', 'nom_du_dirigeant_des_jeunes',  'region', 'groupe', 'ville', 'nombre_de_membres', 'telephone')



