from django.urls import path
from . import views

urlpatterns = [
    # Dashboards
    path('', views.croissance_national, name='croissance_national'),
    path('region/<str:region>/', views.croissance_region, name='croissance_region'),
    path('groupe/<str:groupe>/', views.croissance_groupe, name='croissance_groupe'),
    path('eglise/<int:pk>/', views.croissance_eglise, name='croissance_eglise'),

    # CRUD nouveaux venus
    path('liste/', views.nouveau_venu_liste, name='nouveau_venu_liste'),
    path('ajouter/', views.nouveau_venu_add, name='nouveau_venu_add'),
    path('modifier/<int:pk>/', views.nouveau_venu_edit, name='nouveau_venu_edit'),
    path('supprimer/<int:pk>/', views.nouveau_venu_delete, name='nouveau_venu_delete'),
]
