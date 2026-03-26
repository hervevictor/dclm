from django.urls import path
from .views import *

urlpatterns = [
    path('liste/jeunes', JeuneList.as_view(), name='jeunes'),
    path('jouter/jeune', AddJeune.as_view(), name='add_jeune'),
    path('jeune/<int:pk>', JeuneDetails.as_view(), name='jeune_details'),
    path('jeune/<int:pk>/editer', EditJeune.as_view(), name='edit_jeune'),
    path('jeune/<int:pk>/supprimer', DeleteJeune.as_view(), name='delete_jeune'),
    
    path('district/<str:dist>', FilteJeunesDistrict, name='jeune_district'),
    path('region/<str:regs>', FilteJeunesRegion, name='jeune_region'),
    path('groupe/<str:group>', FilteJeunesGroupe, name='jeune_groupe'),
    
    path('search', SearchJeunes, name='search_jeune'),

]
