from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import RegisterForm, EditUserForm, PasswordChangingForm, UserProfileForm
from .models import UserProfile
from .utils import RBACMixin, AdminOnlyMixin, admin_required


class UserRegister(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')


class UserEditeProfile(RBACMixin, UpdateView):
    form_class = EditUserForm
    template_name = 'registration/edit_compte.html'
    success_url = reverse_lazy('dashboard')  # Redirige vers le tableau de bord, pas login

    def get_object(self):
        return self.request.user


def password_success(request):
    return render(request, 'registration/password_success.html', {})


class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordChangingForm  # Utilise le bon formulaire personnalisé
    success_url = reverse_lazy('password_success')


# ─── Gestion des utilisateurs (ADMIN uniquement) ───────────────────────────────

class UserListView(AdminOnlyMixin, UpdateView):
    """Vue réservée aux ADMIN pour voir et gérer tous les utilisateurs."""
    pass  # Remplacé par la FBV ci-dessous pour plus de flexibilité


@login_required(login_url='/membres/login/')
def profil(request):
    """Page de profil de l'utilisateur connecté."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'registration/profil.html', {'profile': profile})


@admin_required
def user_list(request):
    """Liste tous les utilisateurs avec leur profil RBAC."""
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'registration/user_list.html', {'users': users})


@admin_required
def user_edit_rbac(request, user_id):
    """Permet à un ADMIN de modifier le niveau d'accès et les assignations d'un utilisateur."""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Profil de {target_user.username} mis à jour.")
            return redirect('user_list')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'registration/user_edit_rbac.html', {
        'form': form,
        'target_user': target_user,
    })


@admin_required
def user_toggle_active(request, user_id):
    """Active ou désactive un compte utilisateur."""
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('user_list')
    target_user.is_active = not target_user.is_active
    target_user.save()
    status = "activé" if target_user.is_active else "désactivé"
    messages.success(request, f"Compte de {target_user.username} {status}.")
    return redirect('user_list')
