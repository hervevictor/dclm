from django.urls import path
from .views import *

urlpatterns = [
  
    path('liste/enfants', EnfantList.as_view(), name='enfants'),
    path('jouter/enfant', AddEnfant.as_view(), name='add_enfant'),
    path('enfant/<int:pk>', EnfantDetails.as_view(), name='enfant_details'),
    path('enfant/<int:pk>/editer', EditEnfant.as_view(), name='edit_enfant'),
    path('enfant/<int:pk>/supprimer', DeleteEnfant.as_view(), name='delete_enfant'),
    
    path('district/<str:dist>', FilteEnfantsDistrict, name='enfants_district'),
    path('groupe/<str:group>', FilteEnfantsGroupe, name='enfants_groupe'),
    path('region/<str:regs>', FilteEnfantsRegion, name='enfants_region'),
    
    path('search_enfant', SearchEnfants, name='search_enfant'),
    
]
