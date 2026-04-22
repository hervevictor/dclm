from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from dateutil.relativedelta import relativedelta

from Eglises.models import Eglise, Region, Groupe
from Adultes.models import Adulte
from Jeunes_app.models import Jeune
from Enfants.models import Enfant
from Seances.models import Bilan
from GCK.models import BilanGCK, BilanConferenceMinistres, BilanImpact
from Croissance.models import NouveauVenu
from Quotas.models import QuotaEglise, VersementQuota
from Finances.models import Versement


def _sum(qs, field):
    return int(qs.aggregate(s=Sum(field))['s'] or 0)


def _pct(a, b):
    return round(a * 100 / b) if b else 0


@login_required(login_url='/membres/login/')
def dashboard(request):
    today = date.today()
    annee = today.year

    # ── Structure ──────────────────────────────────────────────────────────────
    nb_regions = Region.objects.count()
    nb_groupes = Groupe.objects.count()
    nb_eglises = Eglise.objects.count()

    # ── Membres ────────────────────────────────────────────────────────────────
    a_h = Adulte.objects.filter(sexe='Masculin').count()
    a_f = Adulte.objects.filter(sexe='Feminin').count()
    j_h = Jeune.objects.filter(sexe='Masculin').count()
    j_f = Jeune.objects.filter(sexe='Feminin').count()
    e_h = Enfant.objects.filter(sexe='Masculin').count()
    e_f = Enfant.objects.filter(sexe='Feminin').count()
    total_membres = a_h + a_f + j_h + j_f + e_h + e_f

    # Membres par région
    membres_par_region = []
    for region in Region.objects.order_by('name'):
        kw = {'eglise__region': region.name}
        ra = Adulte.objects.filter(**kw).count()
        rj = Jeune.objects.filter(**kw).count()
        re = Enfant.objects.filter(**kw).count()
        membres_par_region.append({
            'region': region.name,
            'adultes': ra,
            'jeunes': rj,
            'enfants': re,
            'total': ra + rj + re,
        })

    # ── Séances — mois en cours ────────────────────────────────────────────────
    bilans_mois = Bilan.objects.filter(date__year=annee, date__month=today.month)
    s_ah = _sum(bilans_mois, 'adultes_hommes')
    s_af = _sum(bilans_mois, 'adultes_femmes')
    s_jh = _sum(bilans_mois, 'jeunes_garcons')
    s_jf = _sum(bilans_mois, 'jeunes_filles')
    s_eh = _sum(bilans_mois, 'enfants_garcons')
    s_ef = _sum(bilans_mois, 'enfants_filles')
    s_cotis = _sum(bilans_mois, 'cotisation')
    s_total = s_ah + s_af + s_jh + s_jf + s_eh + s_ef

    # Évolution séances — 6 derniers mois
    debut_6m = today.replace(day=1) - relativedelta(months=5)
    evolution_seances = (
        Bilan.objects.filter(date__gte=debut_6m)
        .annotate(mois=TruncMonth('date'))
        .values('mois')
        .annotate(
            total=Sum('adultes_hommes') + Sum('adultes_femmes') +
                  Sum('jeunes_garcons') + Sum('jeunes_filles') +
                  Sum('enfants_garcons') + Sum('enfants_filles'),
            cotis=Sum('cotisation'),
        )
        .order_by('mois')
    )
    chart_labels = []
    chart_presence = []
    chart_cotis = []
    MOIS_FR = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    for row in evolution_seances:
        chart_labels.append(MOIS_FR[row['mois'].month - 1])
        chart_presence.append(int(row['total'] or 0))
        chart_cotis.append(float(row['cotis'] or 0))

    # ── GCK — année en cours ───────────────────────────────────────────────────
    gck_annee = BilanGCK.objects.filter(date__year=annee)
    gck_ah = _sum(gck_annee, 'adultes_hommes')
    gck_af = _sum(gck_annee, 'adultes_femmes')
    gck_jh = _sum(gck_annee, 'jeunes_hommes')
    gck_jf = _sum(gck_annee, 'jeunes_femmes')
    gck_enf = _sum(gck_annee, 'enfants')
    gck_conv = _sum(gck_annee, 'nouveaux_convertis')
    gck_total = gck_ah + gck_af + gck_jh + gck_jf + gck_enf

    conf_annee = BilanConferenceMinistres.objects.filter(date__year=annee)
    conf_total = (_sum(conf_annee, 'adultes_hommes') + _sum(conf_annee, 'adultes_femmes') +
                  _sum(conf_annee, 'jeunes_hommes') + _sum(conf_annee, 'jeunes_femmes') +
                  _sum(conf_annee, 'enfants'))

    impact_annee = BilanImpact.objects.filter(date__year=annee)
    impact_total = (_sum(impact_annee, 'adultes_hommes') + _sum(impact_annee, 'adultes_femmes') +
                    _sum(impact_annee, 'jeunes_hommes') + _sum(impact_annee, 'jeunes_femmes') +
                    _sum(impact_annee, 'enfants'))

    # ── Quotas ─────────────────────────────────────────────────────────────────
    q_total = int(QuotaEglise.objects.filter(annee=annee).aggregate(s=Sum('montant'))['s'] or 0)
    q_verse = int(VersementQuota.objects.aggregate(s=Sum('montant'))['s'] or 0)
    q_reste = q_total - q_verse
    q_pct = _pct(q_verse, q_total)

    # ── Croissance ─────────────────────────────────────────────────────────────
    nv_annee = NouveauVenu.objects.filter(date_venue__year=annee)
    nv_total = nv_annee.count()
    nv_restes = nv_annee.filter(statut='RESTE').count()
    nv_partis = nv_annee.filter(statut='PARTI').count()
    nv_suivis = nv_annee.filter(statut='SUIVI').count()
    nv_retention = _pct(nv_restes, nv_total)

    # ── Versements cotisations ─────────────────────────────────────────────────
    cotis_annee = int(Versement.objects.filter(date__year=annee).aggregate(s=Sum('montant'))['s'] or 0)

    context = {
        'today': today, 'annee': annee,
        'nb_regions': nb_regions, 'nb_groupes': nb_groupes, 'nb_eglises': nb_eglises,
        'a_h': a_h, 'a_f': a_f,
        'j_h': j_h, 'j_f': j_f,
        'e_h': e_h, 'e_f': e_f,
        'total_membres': total_membres,
        'membres_par_region': membres_par_region,
        's_ah': s_ah, 's_af': s_af,
        's_jh': s_jh, 's_jf': s_jf,
        's_eh': s_eh, 's_ef': s_ef,
        's_total': s_total, 's_cotis': s_cotis,
        's_nb_bilans': bilans_mois.count(),
        'chart_labels': chart_labels,
        'chart_presence': chart_presence,
        'chart_cotis': chart_cotis,
        'gck_ah': gck_ah, 'gck_af': gck_af,
        'gck_jh': gck_jh, 'gck_jf': gck_jf,
        'gck_enf': gck_enf, 'gck_conv': gck_conv,
        'gck_total': gck_total,
        'conf_total': conf_total, 'impact_total': impact_total,
        'q_total': q_total, 'q_verse': q_verse,
        'q_reste': q_reste, 'q_pct': q_pct,
        'nv_total': nv_total, 'nv_restes': nv_restes,
        'nv_partis': nv_partis, 'nv_suivis': nv_suivis,
        'nv_retention': nv_retention,
        'cotis_annee': cotis_annee,
    }
    return render(request, 'Dashboard/dashboard.html', context)
