from django.urls import path
from .views import *

urlpatterns = [
    path('seances', seances, name='seances'),
    path('add_bilan', add_bilan, name='add_bilan'),
    path('seance/<int:id>', seance_details, name='seance_details'),
    path('seance/<int:pk>/edit', EditSeance.as_view(), name='edit_seance'),
    path('seance/<int:pk>/delete', DeleteSeance.as_view(), name='delete_seance'),
    
    path('group_totals/', group_view, name='group_totals'),
    path('region_totals/', region_view, name='region_totals'),
    path('seance_filter/<str:seance_type>/', seance_filter_jour, name='seance_filter'),
    
    path('group/<int:groupe_id>/seance/<str:seance_type>/', group_seance_filter, name='group_seance_filter'),
    path('region/<str:region_name>/seance/<str:seance_type>/', region_seance_filter, name='region_seance_filter'),
    
    #path('region/<str:region_name>/seance/<str:seance_type>/', region_seance_filter, name='region_seance_filter'),
    #path('group/<int:groupe_id>/seance/<str:seance_type>/', seance_groupe_filter, name='seance_groupe_filter'),
]
