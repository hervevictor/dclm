from django import forms
from .models import Transaction
from Eglises.models import Eglise

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['titre', 'type_transaction', 'montant', 'description', 'date', 'eglise']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'type_transaction': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'eglise': forms.Select(attrs={'class': 'form-control select-search'}),
        }
