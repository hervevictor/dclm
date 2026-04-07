from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_transaction', 'montant', 'date', 'eglise', 'auteur')
    list_filter = ('type_transaction', 'date', 'eglise')
    search_fields = ('titre', 'description')
