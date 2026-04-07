from django.urls import path
from . import views

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
]
