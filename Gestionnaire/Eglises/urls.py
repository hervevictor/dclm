from django.urls import path
from .views import *

urlpatterns = [
               
    path('', index, name='index'),
    path('dashboard', dashboard, name='dashboard'),          
    
    
    path('eglises', EgliseList.as_view(), name='eglises'),
    path('eglise/jouter/', AddEglise.as_view(), name='add_eglise'),
    path('eglise/<int:pk>', EgliseDetails.as_view(), name='eglise_details'),
    path('eglise/<int:pk>/editer', EditEglise.as_view(), name='edit_eglise'),
    path('eglise/<int:pk>/supprimer', DeleteEglise.as_view(), name='delete_eglise'),
    
    path('eglise/<str:group>', EgliseGroupe, name='eglises_groupe'),
    path('eglise/region/<str:regs>', EgliseRegion, name='eglises_region'),
    
        
    
    
    path('groupe/ajouter', AddGroupe.as_view(), name='add_groupe'),
    path('groupes', Groupes, name='groupe_liste'),
    path('groupe/<int:id>', groupeDetails, name='groupe_details'),
    path('groupe/<str:pk>/edit', EditGroupe, name='edit_groupe'),
    path('groupe/<int:pk>/delete', DeleteGroupe, name='delete_groupe'),
    path('groupes/region/<str:regs>', FiltreGroupeRegion, name='groupe_region'),

    path('regions/', region_list, name='region_list'),
    path('regions/ajouter/', add_region, name='add_region'),
    path('regions/<int:pk>/', region_details, name='region_details'),
    path('regions/<int:pk>/modifier/', edit_region, name='edit_region'),
    path('regions/<int:pk>/supprimer/', delete_region, name='delete_region'),

    path('membres/export/', export_membres_view, name='export_membres'),
]


