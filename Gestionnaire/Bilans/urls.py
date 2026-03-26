from django.urls import path
from .views import *


urlpatterns = [
    path('add_cellules', AddCellules.as_view(), name='add_cellules'),
    path('cellules_list', CellulesList.as_view(), name='cellules_list'),
    path('cellule/<int:id>', CellulesDetaill, name='cellules_detail'),
    path('cellule/<int:pk>/edit', EditCellules.as_view(), name='edit_cellules'),
    path('cellule/<int:pk>/remove', DeleteCellules.as_view(), name='delete_cellules'),
    path('cellules_groups/<str:group>', FilterCellulesGroups, name='cellules_groups'),
    path('cellules_region/<str:regs>', FilterCellulesRegion, name='cellules_region'),
    path('cellules_district/<str:dist>', FilterCellulesDistricts, name='cellules_district'),
    path('cellules_section/<str:sect>', CellulesSection, name='cellules_section'),
    
    path('add_evenements', AddEvenements.as_view(), name='add_evenements'),
    path('evenements_list', EvenementsList.as_view(), name='evenements_list'),
    path('evenements/<int:id>', EvenementsDetail, name='evenements_detail'),
    path('evenements/<int:pk>/edit', EditEvenements.as_view(), name='edit_evenements'),
    path('evenements/<int:pk>/remove', DeleteEvenements.as_view(), name='delete_evenements'),
]
