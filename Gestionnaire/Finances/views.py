from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.urls import reverse_lazy
from .models import Transaction
from .forms import TransactionForm
from Membres.utils import filter_by_rbac, AdminComptableMixin


class TransactionListView(AdminComptableMixin, ListView):
    model = Transaction
    template_name = 'Finances/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_by_rbac(self.request.user, qs, 'transaction')

        region = self.request.GET.get('region')
        groupe = self.request.GET.get('groupe')
        district = self.request.GET.get('district')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if region:
            qs = qs.filter(eglise__region__icontains=region)
        if groupe:
            qs = qs.filter(eglise__groupe__icontains=groupe)
        if district:
            qs = qs.filter(eglise__nom__icontains=district)
        if start_date and end_date:
            qs = qs.filter(date__range=[start_date, end_date])

        return qs.order_by('eglise__region', 'eglise__groupe', 'eglise__nom', '-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['total_entrees'] = sum(t.montant for t in qs if t.type_transaction == 'ENTREE')
        context['total_sorties'] = sum(t.montant for t in qs if t.type_transaction == 'SORTIE')
        context['solde'] = context['total_entrees'] - context['total_sorties']
        return context


class TransactionCreateView(AdminComptableMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'Finances/transaction_form.html'
    success_url = reverse_lazy('transaction_list')

    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(AdminComptableMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'Finances/transaction_form.html'
    success_url = reverse_lazy('transaction_list')


class TransactionDeleteView(AdminComptableMixin, DeleteView):
    model = Transaction
    template_name = 'Finances/transaction_confirm_delete.html'
    success_url = reverse_lazy('transaction_list')


class TransactionDetailView(AdminComptableMixin, DetailView):
    model = Transaction
    template_name = 'Finances/transaction_detail.html'
