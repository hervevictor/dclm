from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Eglise, Groupe, Region
from .forms import EgliseForm, GroupeForm, RegionForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

from Adultes.resources import EgliseResources
from django.http import HttpResponse
from tablib import Dataset
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from Jeunes_app.models import Jeune
from Adultes.models import Adulte
from Enfants.models import Enfant

from Annonces.models import Message, Annonce
from datetime import timedelta
from django.utils import timezone
from Membres.utils import filter_by_rbac, RBACMixin, AdminOnlyMixin


# ─── Helper statistiques membres ───────────────────────────────────────────────

def get_member_stats(**filter_kwargs):
    """
    Retourne la composition H/F par catégorie (Adultes, Jeunes, Enfants) + totaux.
    Passer les filtres Django standard, ex: eglise=obj, eglise__groupe='Adidogomé'
    """
    a_h = Adulte.objects.filter(sexe='Masculin', **filter_kwargs).count()
    a_f = Adulte.objects.filter(sexe='Feminin',  **filter_kwargs).count()
    j_h = Jeune.objects.filter(sexe='Masculin',  **filter_kwargs).count()
    j_f = Jeune.objects.filter(sexe='Feminin',   **filter_kwargs).count()
    e_h = Enfant.objects.filter(sexe='Masculin', **filter_kwargs).count()
    e_f = Enfant.objects.filter(sexe='Feminin',  **filter_kwargs).count()
    return {
        'adultes_h':     a_h,
        'adultes_f':     a_f,
        'adultes_total': a_h + a_f,
        'jeunes_h':      j_h,
        'jeunes_f':      j_f,
        'jeunes_total':  j_h + j_f,
        'enfants_h':     e_h,
        'enfants_f':     e_f,
        'enfants_total': e_h + e_f,
        'total_h':       a_h + j_h + e_h,
        'total_f':       a_f + j_f + e_f,
        'total':         a_h + a_f + j_h + j_f + e_h + e_f,
    }



@login_required(login_url='/membres/login/')
def index(request):
    date_limit_msg = timezone.now().date() - timedelta(days=6)
    date_limit_ann = timezone.now().date() - timedelta(days=30)

    recent_messages = Message.objects.filter(date__gt=date_limit_msg).order_by('-date')
    recent_annonces = Annonce.objects.filter(add_date__gt=date_limit_ann).order_by('-add_date')

    regions_qs = Region.objects.all().order_by('name')
    groupes = Groupe.objects.all().order_by('region', 'name')
    eglises = Eglise.objects.all().order_by('region', 'groupe', 'nom')

    # Comptes par région
    from django.db.models import Count
    groupes_count = {
        item['region']: item['c']
        for item in Groupe.objects.values('region').annotate(c=Count('id'))
    }
    eglises_count = {
        item['region']: item['c']
        for item in Eglise.objects.values('region').annotate(c=Count('id'))
    }

    regions = [
        {
            'obj': r,
            'name': r.name,
            'nom_du_pasteur_regional': r.nom_du_pasteur_regional,
            'nombre_de_membres': r.nombre_de_membres,
            'nb_groupes': groupes_count.get(r.name, 0),
            'nb_eglises': eglises_count.get(r.name, 0),
        }
        for r in regions_qs
    ]

    return render(request, 'index.html', {
        'messages_recents': recent_messages,
        'annonces_recentes': recent_annonces,
        'regions': regions,
        'groupes': groupes,
        'eglises': eglises,
        'message': recent_messages.first(),
        'annonce': recent_annonces.first(),
    })


@login_required(login_url='/membres/login/')
def dashboard(request):
    user = request.user

    # Seuls les admins et le compte national (COMPTABLE) ont accès au dashboard
    if not user.is_superuser:
        profile = getattr(user, 'profile', None)
        if not profile or profile.niveau_acces not in ('ADMIN', 'COMPTABLE'):
            return redirect('eglises')

    eglises = filter_by_rbac(user, Eglise.objects.all(), 'eglise').count()
    groupes = filter_by_rbac(user, Groupe.objects.all(), 'groupe').count()
    regions = filter_by_rbac(user, Region.objects.all(), 'region').count()
    adultes = filter_by_rbac(user, Adulte.objects.all(), 'adulte').count()
    jeunes = filter_by_rbac(user, Jeune.objects.all(), 'jeune').count()
    enfants = filter_by_rbac(user, Enfant.objects.all(), 'enfant').count()
    
    context = {
        'eglises':eglises,
        'groupes':groupes,
        'regions':regions,
        'adultes':adultes,
        'jeunes':jeunes,
        'enfants':enfants
    }
    return render(request, 'dashboard.html', context)



class AddEglise(RBACMixin, CreateView):
    model = Eglise
    form_class = EgliseForm
    template_name = 'Eglises/add_eglise.html'


class EgliseList(ListView):
    model = Eglise
    template_name = 'Eglises/eglise_liste.html'

    def get_queryset(self):
        # Accessible à tous (connecté ou non) — affiche toutes les églises
        return Eglise.objects.all()

    def get_context_data(self, *args, **kwargs):
        context = super(EgliseList, self).get_context_data(*args, **kwargs)
        context["eglises_nombre"] = self.get_queryset().count()
        return context


class EgliseDetails(DetailView):
    model = Eglise
    template_name = 'Eglises/eglise_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['peut_modifier'] = can_edit_eglise(self.request.user, self.object)
        context['peut_supprimer'] = (
            self.request.user.is_authenticated and (
                self.request.user.is_superuser or (
                    hasattr(self.request.user, 'profile') and
                    self.request.user.profile.niveau_acces == 'ADMIN'
                )
            )
        )
        context['stats'] = get_member_stats(eglise=self.object)
        return context


def can_edit_eglise(user, eglise):
    """Retourne True si l'utilisateur a le droit de modifier cette église."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'profile'):
        return False
    profil = user.profile
    if profil.niveau_acces in ['ADMIN', 'COMPTABLE']:
        return True
    if profil.niveau_acces == 'REGION' and profil.region_assignee:
        return eglise.region.strip().lower() == profil.region_assignee.strip().lower()
    if profil.niveau_acces == 'GROUPE' and profil.groupe_assigne:
        return eglise.groupe.strip().lower() == profil.groupe_assigne.strip().lower()
    if profil.niveau_acces == 'DISTRICT' and profil.district_assigne:
        return eglise.nom.strip().lower() == profil.district_assigne.strip().lower()
    return False


class EditEglise(RBACMixin, UpdateView):
    model = Eglise
    form_class = EgliseForm
    template_name = 'Eglises/edit_Eglise.html'

    def dispatch(self, request, *args, **kwargs):
        eglise = self.get_object()
        if not can_edit_eglise(request.user, eglise):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DeleteEglise(AdminOnlyMixin, DeleteView):
    model = Eglise
    template_name = 'Eglises/delete_Eglise.html'
    success_url = reverse_lazy('eglises')


# Search eglise se trouve dans annonce pour raison d'erreurs infondées
    

def EgliseGroupe(request, group):
    groupes = Groupe.objects.all()
    eglises = Eglise.objects.filter(groupe=group)
    eglise_nombre = eglises.count()
    
    resource = EgliseResources()
    
    if request.method == 'POST':
        # Get selected option from form
        file_format = request.POST['file-format']
        dataset = resource.export(eglises)
        
        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
            return response
        elif file_format == 'PDF':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="eglises_.pdf"'
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Table data
            data = [["Nom", "Pasteur", "Dirigeant J", "Dirigeant E", "groupe", "Region", 'N membres', 'telephone']]
            for eglise in eglises:
                data.append([eglise.nom, eglise.nom_du_pasteur, eglise.nom_du_dirigeant_des_jeunes, eglise.nom_du_dirigeant_des_enfants, eglise.groupe, eglise.region, eglise.nombre_de_membres, eglise.telephone])

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(dataset.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
            return response
    
    context = {
        'eglises' : eglises,
        'eglise_nombre' : eglise_nombre,
        'groupes' : groupes,
        'group' : group
    }
    return render(request, 'Eglises/eglise_groupe.html', context)


def EgliseRegion(request, regs):
    region = Region.objects.all()
    eglises = Eglise.objects.filter(region=regs)
    eglise_nombre = eglises.count()
    
    context = {
        'eglises' : eglises,
        'eglise_nombre' : eglise_nombre,
        'regs' : regs
    }
    return render(request, 'Eglises/eglise_region.html', context)



''' Groupes '''

class AddGroupe(RBACMixin, CreateView):
    model = Groupe
    form_class = GroupeForm
    template_name = 'Groupes/add_groupe.html'


@login_required(login_url='/membres/login/')
def Groupes(request):
    groupes = Groupe.objects.all()
    groupes_nombre = groupes.count()
    
    context = {
        'groupes' : groupes,
        'groupes_nombre' : groupes_nombre
    }
    return render(request, 'Groupes/groupe_liste.html', context)

@login_required(login_url='/membres/login/')
def groupeDetails(request, id):
    groupe = get_object_or_404(Groupe, pk=id)
    eglises = Eglise.objects.filter(groupe=groupe.name).order_by('nom')
    # Stats calculées depuis les membres réels de chaque église du groupe
    eglises_stats = []
    for e in eglises:
        s = get_member_stats(eglise=e)
        eglises_stats.append({'eglise': e, 'stats': s})
    stats = get_member_stats(eglise__groupe=groupe.name)
    context = {
        'groupe': groupe,
        'eglises': eglises,
        'eglises_stats': eglises_stats,
        'nb_eglises': eglises.count(),
        'stats': stats,
    }
    return render(request, 'Groupes/groupe_details.html', context)

@login_required(login_url='/membres/login/')
def EditGroupe(request, pk):
    groupe = Groupe.objects.get(id=pk)
    form = GroupeForm(instance=groupe)
    if request.method == 'POST':
        form = GroupeForm(request.POST, instance=groupe)
        if form.is_valid():
            form.save()
            return redirect('groupe_details', id=groupe.pk)
    
    context = {
        'form' : form,
        'groupe' : groupe,
    }
    return render(request, 'Groupes/edit_groupe.html', context)

@login_required(login_url='/membres/login/')
def DeleteGroupe(request, pk):
    groupe = Groupe.objects.get(id=pk)
    if request.method == 'POST':
        groupe.delete()
        return redirect('groupe_liste')
    
    context = {
        'groupe': groupe,
    }
    return render(request, 'Groupes/delete_groupe.html', context)

 
@login_required(login_url='/membres/login/')
def FiltreGroupeRegion(request, regs):
    groupe_region = Groupe.objects.filter(region=regs)
    groupe_region_count = groupe_region.count()
    context = {
        'groupe_region':groupe_region,
        'groupe_region_count':groupe_region_count,
        'regs':regs
    }
    return render(request, 'Groupes/groupe_region.html', context)


# ─── Régions ───────────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def add_region(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = RegionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        region = form.save()
        return redirect('region_details', pk=region.pk)
    return render(request, 'Regions/region_form.html', {'form': form, 'titre': 'Ajouter une région'})


@login_required(login_url='/membres/login/')
def edit_region(request, pk):
    region = get_object_or_404(Region, pk=pk)
    peut_modifier = (
        request.user.is_superuser or
        (hasattr(request.user, 'profile') and
         request.user.profile.niveau_acces in ('ADMIN', 'REGION'))
    )
    if not peut_modifier:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = RegionForm(request.POST or None, instance=region)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('region_details', pk=region.pk)
    return render(request, 'Regions/region_form.html', {'form': form, 'region': region, 'titre': 'Modifier la région'})


@login_required(login_url='/membres/login/')
def delete_region(request, pk):
    region = get_object_or_404(Region, pk=pk)
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.niveau_acces == 'ADMIN')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST':
        region.delete()
        return redirect('region_list')
    return render(request, 'Regions/region_delete.html', {'region': region})


@login_required(login_url='/membres/login/')
def region_list(request):
    regions = Region.objects.all().order_by('name')
    context = {
        'regions': regions,
        'regions_count': regions.count(),
    }
    return render(request, 'Regions/region_liste.html', context)


@login_required(login_url='/membres/login/')
def region_details(request, pk):
    region = get_object_or_404(Region, pk=pk)
    groupes = Groupe.objects.filter(region=region.name).order_by('name')
    eglises = Eglise.objects.filter(region=region.name).order_by('nom')
    # Stats membres calculées (pas le champ manuel)
    stats = get_member_stats(eglise__region=region.name)
    # Stats par groupe pour le tableau
    groupes_stats = []
    for g in groupes:
        s = get_member_stats(eglise__groupe=g.name)
        groupes_stats.append({'groupe': g, 'stats': s})
    # Totaux par église pour le tableau des églises
    eglises_avec_total = []
    for e in eglises:
        total = (Adulte.objects.filter(eglise=e).count() +
                 Jeune.objects.filter(eglise=e).count() +
                 Enfant.objects.filter(eglise=e).count())
        eglises_avec_total.append({'eglise': e, 'total': total})
    peut_modifier = (
        request.user.is_superuser or
        (hasattr(request.user, 'profile') and
         request.user.profile.niveau_acces in ('ADMIN', 'REGION'))
    )
    context = {
        'region': region,
        'groupes': groupes,
        'groupes_stats': groupes_stats,
        'eglises': eglises,
        'eglises_avec_total': eglises_avec_total,
        'nb_groupes': groupes.count(),
        'nb_eglises': eglises.count(),
        'stats': stats,
        'peut_modifier': peut_modifier,
    }
    return render(request, 'Regions/region_details.html', context)


# ─── Export membres ────────────────────────────────────────────────────────────

@login_required(login_url='/membres/login/')
def export_membres_view(request):
    """
    Export PDF ou Excel de la liste des membres selon le niveau géographique.
    Paramètres GET :
      - niveau  : national | region | groupe | eglise
      - valeur  : nom de région/groupe ou pk d'église (inutilisé pour national)
      - fmt     : PDF | XLS
    """
    from .exports_membres import export_membres
    niveau = request.GET.get('niveau', 'national')
    valeur = request.GET.get('valeur', '')
    fmt    = request.GET.get('fmt', 'XLS').upper()

    # Pour le niveau église, valeur est un pk entier
    if niveau == 'eglise':
        try:
            valeur = int(valeur)
        except (ValueError, TypeError):
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Paramètre 'valeur' invalide.")

    return export_membres(niveau, valeur, fmt)
