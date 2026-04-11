from django.urls import path
from . import views
from . import views_stats

urlpatterns = [
    # API AJAX
    path('api/membres/<int:eglise_pk>/', views.membres_par_eglise, name='membres_par_eglise'),

    # ── VOEUX ──────────────────────────────────────────────────────────────────
    path('', views.voeu_list, name='voeu_list'),
    path('ajouter/', views.add_voeu, name='add_voeu'),
    path('<int:pk>/', views.voeu_detail, name='voeu_detail'),
    path('<int:pk>/modifier/', views.edit_voeu, name='edit_voeu'),
    path('<int:pk>/supprimer/', views.delete_voeu, name='delete_voeu'),
    path('<int:voeu_pk>/versement/ajouter/', views.add_versement_voeu, name='add_versement_voeu'),
    path('versement/<int:pk>/supprimer/', views.delete_versement_voeu, name='delete_versement_voeu'),
    path('versement/<int:pk>/corriger/', views.corriger_versement_voeu, name='corriger_versement_voeu'),
    path('<int:pk>/modifier-montant/', views.modifier_montant_voeu, name='modifier_montant_voeu'),

    # Hiérarchie Voeux
    path('district/<int:eglise_pk>/', views.voeu_district, name='voeu_district'),
    path('groupe/<str:group>/', views.voeu_groupe, name='voeu_groupe'),
    path('region/<str:regs>/', views.voeu_region, name='voeu_region'),
    path('national/', views.voeu_national, name='voeu_national'),

    # ── CONTRIBUTIONS ──────────────────────────────────────────────────────────
    path('contributions/', views.contribution_list, name='contribution_list'),
    path('contributions/ajouter/', views.add_contribution, name='add_contribution'),
    path('contributions/<int:pk>/', views.contribution_detail, name='contribution_detail'),
    path('contributions/<int:pk>/modifier/', views.edit_contribution, name='edit_contribution'),
    path('contributions/<int:pk>/supprimer/', views.delete_contribution, name='delete_contribution'),
    path('contributions/<int:contrib_pk>/versement/ajouter/', views.add_versement_contribution, name='add_versement_contribution'),
    path('contributions/versement/<int:pk>/supprimer/', views.delete_versement_contribution, name='delete_versement_contribution'),
    path('contributions/versement/<int:pk>/corriger/', views.corriger_versement_contribution, name='corriger_versement_contribution'),

    # Hiérarchie Contributions
    path('contributions/district/<int:eglise_pk>/', views.contribution_district, name='contribution_district'),
    path('contributions/groupe/<str:group>/', views.contribution_groupe, name='contribution_groupe'),
    path('contributions/region/<str:regs>/', views.contribution_region, name='contribution_region'),
    path('contributions/national/', views.contribution_national, name='contribution_national'),

    # ── TYPES DE CONTRIBUTION ──────────────────────────────────────────────────
    path('types/', views.type_list, name='type_list'),
    path('types/ajouter/', views.add_type, name='add_type'),
    path('types/<int:pk>/modifier/', views.edit_type, name='edit_type'),
    path('types/<int:pk>/supprimer/', views.delete_type, name='delete_type'),

    # ── STATISTIQUES ──────────────────────────────────────────────────────────
    path('statistiques/', views_stats.stats_voeux_contributions, name='stats_voeux'),
    path('statistiques/api/', views_stats.stats_voeux_api, name='stats_voeux_api'),
    path('membre/<int:adulte_pk>/statistiques/', views_stats.stats_membre, name='stats_membre'),

    # ── HISTORIQUE GLOBAL ──────────────────────────────────────────────────────
    path('historique/', views.historique_global, name='historique_global'),

    # Suppression lignes d'historique
    path('historique/voeu/<int:pk>/supprimer/', views.delete_historique_voeu, name='delete_historique_voeu'),
    path('historique/contribution/<int:pk>/supprimer/', views.delete_historique_contribution, name='delete_historique_contribution'),
    path('historique/versement-voeu/<int:pk>/supprimer/', views.delete_historique_versement_voeu, name='delete_historique_versement_voeu'),
    path('historique/versement-contribution/<int:pk>/supprimer/', views.delete_historique_versement_contribution, name='delete_historique_versement_contribution'),

    # Vider tout l'historique d'un objet
    path('<int:voeu_pk>/vider-historique/', views.vider_historiques_voeu, name='vider_historiques_voeu'),
    path('<int:voeu_pk>/vider-corrections-versements/', views.vider_corrections_versements_voeu, name='vider_corrections_versements_voeu'),
    path('contributions/<int:contrib_pk>/vider-historique/', views.vider_historiques_contribution, name='vider_historiques_contribution'),
    path('contributions/<int:contrib_pk>/vider-corrections-versements/', views.vider_corrections_versements_contribution, name='vider_corrections_versements_contribution'),
]
