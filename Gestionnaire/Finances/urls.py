from django.urls import path
from . import views

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),

    # Versements
    path('versements/', views.VersementListView.as_view(), name='versement_list'),
    path('versements/add/', views.VersementCreateView.as_view(), name='versement_add'),
    path('versements/<int:pk>/', views.VersementDetailView.as_view(), name='versement_detail'),
    path('versements/<int:pk>/delete/', views.VersementDeleteView.as_view(), name='versement_delete'),

    # Reliquat
    path('reliquat/', views.reliquat_national, name='reliquat_national'),
    path('reliquat/region/<str:region>/', views.reliquat_region, name='reliquat_region'),
    path('reliquat/groupe/<str:groupe>/', views.reliquat_groupe, name='reliquat_groupe'),
]
