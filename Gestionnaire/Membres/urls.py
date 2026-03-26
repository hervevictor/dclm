from django.urls import path
from .views import *

urlpatterns = [
    path('register/', UserRegister.as_view(), name='register'),
    path('edit_profile/', UserEditeProfile.as_view(), name="edit_profile"),
    path('password/', PasswordsChangeView.as_view(template_name='registration/change_password.html')),
    path('password_success', password_success, name='password_success'),
]


