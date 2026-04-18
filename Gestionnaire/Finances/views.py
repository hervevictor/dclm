from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Transaction, Versement
from .forms import TransactionForm, VersementForm
from Membres.utils import filter_by_rbac, AdminComptableMixin
from Eglises.models import Eglise, Groupe, Region
from Seances.models import Bilan


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


# ─── Versements ───────────────────────────────────────────────────────────────

class VersementListView(LoginRequiredMixin, ListView):
    model = Versement
    template_name = 'Finances/versement_list.html'
    context_object_name = 'versements'

    def get_queryset(self):
        qs = Versement.objects.select_related('eglise', 'auteur')
        user = self.request.user
        if not user.is_superuser and hasattr(user, 'profile'):
            p = user.profile
            if p.niveau_acces == 'REGION' and p.region_assignee:
                qs = qs.filter(eglise__region=p.region_assignee)
            elif p.niveau_acces == 'GROUPE' and p.groupe_assigne:
                qs = qs.filter(eglise__groupe=p.groupe_assigne)
            elif p.niveau_acces == 'DISTRICT' and p.district_assigne:
                qs = qs.filter(eglise__nom=p.district_assigne)
        return qs.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['total_verse'] = qs.aggregate(s=Sum('montant'))['s'] or 0
        return context


class VersementCreateView(LoginRequiredMixin, CreateView):
    model = Versement
    form_class = VersementForm
    template_name = 'Finances/versement_form.html'
    success_url = reverse_lazy('versement_list')

    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)


class VersementDetailView(LoginRequiredMixin, DetailView):
    model = Versement
    template_name = 'Finances/versement_detail.html'


class VersementDeleteView(AdminComptableMixin, DeleteView):
    model = Versement
    template_name = 'Finances/versement_confirm_delete.html'
    success_url = reverse_lazy('versement_list')


# ─── Reliquat par église / groupe / région ────────────────────────────────────

def _reliquat_eglise(eglise):
    """Retourne (total_cotisé, total_versé, reliquat) pour une église."""
    cotise = Bilan.objects.filter(eglise=eglise).aggregate(s=Sum('cotisation'))['s'] or 0
    verse  = Versement.objects.filter(eglise=eglise).aggregate(s=Sum('montant'))['s'] or 0
    return int(cotise), int(verse), int(cotise) - int(verse)


@login_required(login_url='/membres/login/')
def reliquat_national(request):
    eglises = Eglise.objects.all().order_by('region', 'groupe', 'nom')
    rows = []
    total_cotise = total_verse = 0
    for e in eglises:
        c, v, r = _reliquat_eglise(e)
        rows.append({'eglise': e, 'cotise': c, 'verse': v, 'reliquat': r})
        total_cotise += c
        total_verse  += v
    context = {
        'rows': rows,
        'total_cotise': total_cotise,
        'total_verse': total_verse,
        'reliquat_total': total_cotise - total_verse,
        'niveau': 'national',
    }
    return render(request, 'Finances/reliquat.html', context)


@login_required(login_url='/membres/login/')
def reliquat_region(request, region):
    eglises = Eglise.objects.filter(region=region).order_by('groupe', 'nom')
    rows = []
    total_cotise = total_verse = 0
    for e in eglises:
        c, v, r = _reliquat_eglise(e)
        rows.append({'eglise': e, 'cotise': c, 'verse': v, 'reliquat': r})
        total_cotise += c
        total_verse  += v
    context = {
        'rows': rows,
        'total_cotise': total_cotise,
        'total_verse': total_verse,
        'reliquat_total': total_cotise - total_verse,
        'niveau': region,
    }
    return render(request, 'Finances/reliquat.html', context)


@login_required(login_url='/membres/login/')
def reliquat_groupe(request, groupe):
    eglises = Eglise.objects.filter(groupe=groupe).order_by('nom')
    rows = []
    total_cotise = total_verse = 0
    for e in eglises:
        c, v, r = _reliquat_eglise(e)
        rows.append({'eglise': e, 'cotise': c, 'verse': v, 'reliquat': r})
        total_cotise += c
        total_verse  += v
    context = {
        'rows': rows,
        'total_cotise': total_cotise,
        'total_verse': total_verse,
        'reliquat_total': total_cotise - total_verse,
        'niveau': groupe,
    }
    return render(request, 'Finances/reliquat.html', context)


