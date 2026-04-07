from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from .models import UserProfile

# On retire les "Groups" natifs de Django pour ne pas les confondre avec les Groupes d'Églises
admin.site.unregister(Group)
from django.contrib.auth.models import User
from .models import UserProfile

from .forms import UserProfileForm

# Définir l'interface Inline pour ajouter le profil directement dans l'utilisateur
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileForm
    can_delete = False
    verbose_name_plural = 'Profil Utilisateur (Région, Groupe, District)'

# Étendre l'admin User par défaut
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('user', 'niveau_acces', 'region_assignee', 'groupe_assigne', 'district_assigne', 'section_assignee')
    list_filter = ('niveau_acces', 'section_assignee')
    search_fields = ('user__username', 'region_assignee', 'groupe_assigne', 'district_assigne')

# Ré-enregistrer UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
