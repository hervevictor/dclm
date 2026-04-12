"""Export PDF et Excel de la liste des membres (Adultes + Jeunes + Enfants)."""
from io import BytesIO
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from tablib import Dataset

from Adultes.models import Adulte
from Jeunes_app.models import Jeune
from Enfants.models import Enfant


# ─── Style commun ─────────────────────────────────────────────────────────────

def _style():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (2, -2), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f4f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1d4ed8')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ])


# ─── Construction de la liste combinée ────────────────────────────────────────

def _build_rows(filtre):
    """
    Retourne une liste de tuples (nom, prenom, categorie, sexe, eglise, groupe, region).
    filtre: dict kwargs Django à passer aux 3 modèles (ex: {'eglise__groupe': 'Adidogomé'}).
    """
    rows = []

    adultes = Adulte.objects.filter(**filtre).select_related('eglise').order_by(
        'eglise__region', 'eglise__groupe', 'eglise__nom', 'nom')
    for a in adultes:
        rows.append((
            a.nom, a.prenom, 'Adulte', a.sexe,
            a.eglise.nom, a.eglise.groupe, a.eglise.region,
        ))

    jeunes = Jeune.objects.filter(**filtre).select_related('eglise').order_by(
        'eglise__region', 'eglise__groupe', 'eglise__nom', 'nom')
    for j in jeunes:
        rows.append((
            j.nom, j.prenom, 'Jeune', j.sexe,
            j.eglise.nom, j.eglise.groupe, j.eglise.region,
        ))

    enfants = Enfant.objects.filter(**filtre).select_related('eglise').order_by(
        'eglise__region', 'eglise__groupe', 'eglise__nom', 'nom')
    for e in enfants:
        rows.append((
            e.nom, e.prenom, 'Enfant', e.sexe,
            e.eglise.nom, e.eglise.groupe, e.eglise.region,
        ))

    return rows


def _build_filter(niveau, valeur):
    """Construit le dict de filtre selon le niveau géographique."""
    if niveau == 'eglise':
        return {'eglise__pk': valeur}
    if niveau == 'groupe':
        return {'eglise__groupe': valeur}
    if niveau == 'region':
        return {'eglise__region': valeur}
    return {}  # national


def _label(niveau, valeur):
    if niveau == 'eglise':
        try:
            from Eglises.models import Eglise
            e = Eglise.objects.get(pk=valeur)
            return f"Église : {e.nom} — {e.groupe} — {e.region}"
        except Exception:
            return f"Église pk={valeur}"
    if niveau == 'groupe':
        return f"Groupe : {valeur}"
    if niveau == 'region':
        return f"Région : {valeur}"
    return "Liste nationale — tous les membres"


# ─── Export principal ──────────────────────────────────────────────────────────

def export_membres(niveau, valeur, fmt):
    """Point d'entrée unique. niveau ∈ {national, region, groupe, eglise}."""
    filtre = _build_filter(niveau, valeur)
    rows = _build_rows(filtre)
    label = _label(niveau, valeur)

    if fmt == 'XLS':
        return _xlsx(rows, label, niveau)
    return _pdf(rows, label, niveau)


# ─── Excel ────────────────────────────────────────────────────────────────────

def _xlsx(rows, label, niveau):
    ds = Dataset()
    ds.title = 'Membres'
    ds.headers = ['Nom', 'Prénom', 'Catégorie', 'Sexe', 'Église', 'Groupe', 'Région']
    for r in rows:
        ds.append(list(r))
    ds.append(['TOTAL : ' + str(len(rows)), '', '', '', '', '', ''])

    resp = HttpResponse(
        ds.export('xlsx'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    fname = f"membres_{niveau}.xlsx"
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
    return resp


# ─── PDF ──────────────────────────────────────────────────────────────────────

def _pdf(rows, label, niveau):
    resp = HttpResponse(content_type='application/pdf')
    fname = f"membres_{niveau}.pdf"
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("LISTE DES MEMBRES", styles['Title']),
        Paragraph(label, styles['Normal']),
        Spacer(1, 0.4*cm),
    ]

    header = ['Nom', 'Prénom', 'Catégorie', 'Sexe', 'Église', 'Groupe', 'Région']
    data = [header]
    for r in rows:
        data.append([
            str(r[0])[:22], str(r[1])[:22],
            r[2], r[3],
            str(r[4])[:22], str(r[5])[:18], str(r[6])[:15],
        ])
    data.append(['TOTAL : ' + str(len(rows)), '', '', '', '', '', ''])

    col_widths = [4.0*cm, 4.0*cm, 2.2*cm, 2.2*cm, 4.5*cm, 4.0*cm, 3.5*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(_style())
    elements.append(table)

    doc.build(elements)
    resp.write(buf.getvalue())
    buf.close()
    return resp
