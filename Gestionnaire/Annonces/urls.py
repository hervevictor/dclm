from django.urls import path
from .views import *


urlpatterns = [
    
    path('add_message', AddMessage, name='add_message'),
    path('messages', messageList, name='messages'),
    path('message/<int:id>', messageDetails, name='message_details'),
    path('message/<int:pk>/edit', EditMessage.as_view(), name='edite_message'),
    path('message/<int:pk>/delete', DeleteMessage.as_view(), name='delete_message'),

  
    
    path('add_annonces', AddAnnonces.as_view(), name='add_annonces'),
    path('annonces_list', AnnoncesList.as_view(), name='annonces_list'),
    path('annonces/<int:pk>/edit', EditAnnonces.as_view(), name='edit_annonces'),
    path('annonces/<int:pk>/remove', DeleteAnnonces.as_view(), name='delete_annonces'),
    
    path('eglise/search_eglise', SearchEglise, name='search_eglise'),
    
]

