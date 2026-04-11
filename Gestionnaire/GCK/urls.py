from django.urls import path
from . import views
from . import views_conference as vc
from . import views_impact as vi
from . import views_stats as vs

urlpatterns = [
    # ── GCK Soir ──────────────────────────────────────────────────────────────
    path('', views.gck_list, name='gck_list'),
    path('ajouter/', views.add_gck, name='add_gck'),
    path('<int:pk>/', views.gck_detail, name='gck_detail'),
    path('<int:pk>/modifier/', views.EditGCK.as_view(), name='edit_gck'),
    path('<int:pk>/supprimer/', views.DeleteGCK.as_view(), name='delete_gck'),

    path('district/<int:dist_pk>/', views.gck_district, name='gck_district'),
    path('groupe/<str:group>/', views.gck_groupe, name='gck_groupe'),
    path('region/<str:regs>/', views.gck_region, name='gck_region'),
    path('national/', views.gck_national, name='gck_national'),
    path('recapitulatif/', views.gck_recapitulatif, name='gck_recapitulatif'),

    path('convertis/', views.gck_convertis, name='gck_convertis'),
    path('convertis/region/<str:regs>/', views.gck_convertis_region, name='gck_convertis_region'),
    path('convertis/groupe/<str:group>/', views.gck_convertis_groupe, name='gck_convertis_groupe'),

    # ── Vue mensuelle combinée ─────────────────────────────────────────────────
    path('mensuel/', views.gck_mensuel, name='gck_mensuel'),
    path('statistiques/', vs.stats_gck, name='stats_gck'),
    path('statistiques/api/', vs.stats_gck_api, name='stats_gck_api'),

    # ── Conférence des Ministres ───────────────────────────────────────────────
    path('conference/', vc.conference_list, name='conference_list'),
    path('conference/ajouter/', vc.add_conference, name='add_conference'),
    path('conference/<int:pk>/', vc.conference_detail, name='conference_detail'),
    path('conference/<int:pk>/modifier/', vc.EditConference.as_view(), name='edit_conference'),
    path('conference/<int:pk>/supprimer/', vc.DeleteConference.as_view(), name='delete_conference'),
    path('conference/district/<int:dist_pk>/', vc.conference_district, name='conference_district'),
    path('conference/groupe/<str:group>/', vc.conference_groupe, name='conference_groupe'),
    path('conference/region/<str:regs>/', vc.conference_region, name='conference_region'),
    path('conference/national/', vc.conference_national, name='conference_national'),

    # ── Académie d'Impact ─────────────────────────────────────────────────────
    path('impact/', vi.impact_list, name='impact_list'),
    path('impact/ajouter/', vi.add_impact, name='add_impact'),
    path('impact/<int:pk>/', vi.impact_detail, name='impact_detail'),
    path('impact/<int:pk>/modifier/', vi.EditImpact.as_view(), name='edit_impact'),
    path('impact/<int:pk>/supprimer/', vi.DeleteImpact.as_view(), name='delete_impact'),
    path('impact/district/<int:dist_pk>/', vi.impact_district, name='impact_district'),
    path('impact/groupe/<str:group>/', vi.impact_groupe, name='impact_groupe'),
    path('impact/region/<str:regs>/', vi.impact_region, name='impact_region'),
    path('impact/national/', vi.impact_national, name='impact_national'),
]
