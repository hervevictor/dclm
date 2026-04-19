from django.urls import path
from . import views

urlpatterns = [
    # Tableaux de bord
    path('', views.quota_national, name='quota_national'),
    path('region/<str:region>/', views.quota_region, name='quota_region'),
    path('groupe/<str:groupe>/', views.quota_groupe, name='quota_groupe'),

    # Attribution hiérarchique
    path('attribuer/region/', views.quota_attribuer_region, name='quota_attribuer_region'),
    path('attribuer/groupe/', views.quota_attribuer_groupe, name='quota_attribuer_groupe'),
    path('attribuer/groupe/<str:region>/', views.quota_attribuer_groupe, name='quota_attribuer_groupe_region'),
    path('attribuer/eglise/', views.quota_attribuer_eglise, name='quota_attribuer_eglise'),
    path('attribuer/eglise/<str:groupe>/', views.quota_attribuer_eglise, name='quota_attribuer_eglise_groupe'),

    # Détail quota église + promesses
    path('eglises/', views.quota_eglise_list, name='quota_eglise_list'),
    path('eglise/<int:pk>/', views.quota_eglise_detail, name='quota_eglise_detail'),
    path('eglise/<int:quota_pk>/promesse/ajouter/', views.promesse_add, name='promesse_add'),
    path('promesse/<int:pk>/modifier/', views.promesse_edit, name='promesse_edit'),
    path('promesse/<int:pk>/supprimer/', views.promesse_delete, name='promesse_delete'),

    # Versements
    path('versements/', views.versement_quota_list, name='versement_quota_list'),
    path('versements/ajouter/', views.versement_quota_add, name='versement_quota_add'),
    path('versements/supprimer/<int:pk>/', views.versement_quota_supprimer, name='versement_quota_supprimer'),
]
