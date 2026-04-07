from django.urls import path
from . import views

urlpatterns = [
    path('', views.gck_list, name='gck_list'),
    path('ajouter/', views.add_gck, name='add_gck'),
    path('<int:pk>/', views.gck_detail, name='gck_detail'),
    path('<int:pk>/modifier/', views.EditGCK.as_view(), name='edit_gck'),
    path('<int:pk>/supprimer/', views.DeleteGCK.as_view(), name='delete_gck'),

    # Rapports hiérarchiques
    path('district/<int:dist_pk>/', views.gck_district, name='gck_district'),
    path('groupe/<str:group>/', views.gck_groupe, name='gck_groupe'),
    path('region/<str:regs>/', views.gck_region, name='gck_region'),
    path('national/', views.gck_national, name='gck_national'),
]
