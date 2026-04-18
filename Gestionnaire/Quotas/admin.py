from django.contrib import admin
from .models import QuotaRegion, QuotaGroupe, QuotaEglise, VersementQuota


@admin.register(QuotaRegion)
class QuotaRegionAdmin(admin.ModelAdmin):
    list_display = ('region', 'annee', 'montant', 'auteur', 'date_attribution')
    list_filter = ('annee',)


@admin.register(QuotaGroupe)
class QuotaGroupeAdmin(admin.ModelAdmin):
    list_display = ('groupe', 'region', 'annee', 'montant', 'auteur')
    list_filter = ('annee', 'region')


@admin.register(QuotaEglise)
class QuotaEgliseAdmin(admin.ModelAdmin):
    list_display = ('eglise', 'annee', 'montant', 'auteur', 'date_attribution')
    list_filter = ('annee', 'eglise__region', 'eglise__groupe')
    search_fields = ('eglise__nom',)


@admin.register(VersementQuota)
class VersementQuotaAdmin(admin.ModelAdmin):
    list_display = ('eglise', 'montant', 'date', 'auteur')
    list_filter = ('eglise__region', 'eglise__groupe')
    search_fields = ('eglise__nom',)
