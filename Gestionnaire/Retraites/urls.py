from django.urls import path
from . import views

urlpatterns = [
    path('', views.retraite_list, name='retraite_list'),
    path('ajouter/', views.add_retraite, name='add_retraite'),
    path('<int:pk>/', views.retraite_detail, name='retraite_detail'),
    path('<int:pk>/modifier/', views.edit_retraite, name='edit_retraite'),
    path('<int:pk>/supprimer/', views.delete_retraite, name='delete_retraite'),

    # Rapports journaliers
    path('<int:retraite_pk>/jour/ajouter/', views.add_jour_retraite, name='add_jour_retraite'),
    path('jour/<int:pk>/modifier/', views.edit_jour_retraite, name='edit_jour_retraite'),
    path('jour/<int:pk>/supprimer/', views.delete_jour_retraite, name='delete_jour_retraite'),

    # Vues agrégées
    path('region/<str:region_name>/', views.retraite_region, name='retraite_region'),
    path('national/', views.retraite_national, name='retraite_national'),
]
