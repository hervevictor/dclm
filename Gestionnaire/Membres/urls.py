from django.urls import path
from .views import (
    UserRegister, UserEditeProfile, PasswordsChangeView,
    password_success, user_list, user_edit_rbac, user_toggle_active, profil,
)

urlpatterns = [
    path('profil/', profil, name='profil'),
    path('register/', UserRegister.as_view(), name='register'),
    path('edit_profile/', UserEditeProfile.as_view(), name='edit_profile'),
    path('password/', PasswordsChangeView.as_view(template_name='registration/change_password.html'), name='change_password'),
    path('password_success/', password_success, name='password_success'),

    # ── Gestion des utilisateurs (ADMIN uniquement) ──
    path('utilisateurs/', user_list, name='user_list'),
    path('utilisateurs/<int:user_id>/rbac/', user_edit_rbac, name='user_edit_rbac'),
    path('utilisateurs/<int:user_id>/toggle/', user_toggle_active, name='user_toggle_active'),
]
