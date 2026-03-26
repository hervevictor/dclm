from django.urls import path
from .views import *

urlpatterns = [
    path('liste/adutles', AdulteList.as_view(), name='adultes'),
    path('jouter/adute', AddAdulte.as_view(), name='add_adulte'),
    path('adutle/<int:pk>', AdulteDetails.as_view(), name='adulte_details'),
    path('adutle/<int:pk>/editer', EditAdulte.as_view(), name='edit_adulte'),
    path('adutle/<int:pk>/supprimer', DeleteAdulte.as_view(), name='delete_adulte'),
    
    path('district/<str:dist>', FilteAdultesDistrict, name='adulte_district'),
    path('region/<str:regs>', FilteAdultesRegion, name='adulte_region'),
    path('groupe/<str:group>', FilteAdultesGroupe, name='adulte_groupe'),
    
    path('search', SearchAdultes, name='search_adulte'),
 
]
