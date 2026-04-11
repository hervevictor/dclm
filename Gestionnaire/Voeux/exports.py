"""Fonctions d'export PDF et Excel pour Voeux et Contributions."""
from io import BytesIO
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from tablib import Dataset


# ─── Helpers communs ──────────────────────────────────────────────────────────

def _pdf_table_style(n_header_rows=1):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, n_header_rows - 1), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, n_header_rows - 1), colors.white),
        ('FONTNAME', (0, 0), (-1, n_header_rows - 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, n_header_rows), (3, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, n_header_rows), (-1, -2), [colors.white, colors.HexColor('#f0f4f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ])


# ─── VOEUX ────────────────────────────────────────────────────────────────────

def export_voeux(voeux, fmt, label):
    """Exporte la liste des voeux en XLSX ou PDF (avec filtres appliqués)."""
    voeux_list = list(voeux.select_related('membre', 'eglise'))

    if fmt == 'XLS':
        return _voeux_xlsx(voeux_list, label)
    return _voeux_pdf(voeux_list, label)


def _voeux_xlsx(voeux_list, label):
    ds = Dataset()
    ds.title = 'Voeux'
    ds.headers = [
        'Membre', 'Église', 'Groupe', 'Région',
        'Date du voeu', 'Montant promis (FCFA)',
        'Total payé (FCFA)', 'Restant (FCFA)', '% soldé', 'Soldé',
        'Détails',
    ]
    for v in voeux_list:
        ds.append([
            str(v.membre),
            v.eglise.nom,
            v.eglise.groupe,
            v.eglise.region,
            v.date_voeu.strftime('%d/%m/%Y'),
            v.montant_promis,
            v.total_paye,
            v.montant_restant,
            v.pourcentage,
            'Oui' if v.est_solde else 'Non',
            v.details or '',
        ])
    # Ligne totaux
    total_promis = sum(v.montant_promis for v in voeux_list)
    total_paye = sum(v.total_paye for v in voeux_list)
    total_restant = sum(v.montant_restant for v in voeux_list)
    ds.append(['TOTAUX', '', '', '', '', total_promis, total_paye, total_restant, '', '', ''])

    resp = HttpResponse(
        ds.export('xlsx'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    resp['Content-Disposition'] = 'attachment; filename="voeux_export.xlsx"'
    return resp


def _voeux_pdf(voeux_list, label):
    total_promis = sum(v.montant_promis for v in voeux_list)
    total_paye = sum(v.total_paye for v in voeux_list)
    total_restant = sum(v.montant_restant for v in voeux_list)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="voeux_export.pdf"'
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("VOEUX — Export", styles['Title']),
        Paragraph(label, styles['Normal']),
        Spacer(1, 0.4*cm),
    ]

    header = ['Membre', 'Église', 'Groupe', 'Région', 'Date',
              'Promis', 'Payé', 'Restant', '%', 'Soldé']
    data = [header]
    for v in voeux_list:
        data.append([
            str(v.membre)[:25],
            v.eglise.nom[:20],
            v.eglise.groupe[:15],
            v.eglise.region[:12],
            v.date_voeu.strftime('%d/%m/%Y'),
            f"{v.montant_promis:,}",
            f"{v.total_paye:,}",
            f"{v.montant_restant:,}",
            f"{v.pourcentage}%",
            'Oui' if v.est_solde else 'Non',
        ])
    data.append([
        'TOTAUX', '', '', '', '',
        f"{total_promis:,}", f"{total_paye:,}", f"{total_restant:,}", '', '',
    ])

    col_widths = [4.2*cm, 4.0*cm, 3.0*cm, 2.5*cm, 2.2*cm,
                  2.5*cm, 2.5*cm, 2.5*cm, 1.2*cm, 1.2*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(_pdf_table_style())
    elements.append(table)
    doc.build(elements)
    resp.write(buf.getvalue())
    buf.close()
    return resp


# ─── CONTRIBUTIONS ────────────────────────────────────────────────────────────

def export_contributions(contribs, fmt, label):
    """Exporte la liste des contributions en XLSX ou PDF."""
    contribs_list = list(contribs.select_related('membre', 'eglise', 'type_contribution'))

    if fmt == 'XLS':
        return _contribs_xlsx(contribs_list, label)
    return _contribs_pdf(contribs_list, label)


def _contribs_xlsx(contribs_list, label):
    ds = Dataset()
    ds.title = 'Contributions'
    ds.headers = [
        'Membre', 'Église', 'Groupe', 'Région',
        'Type', 'Date', 'Objectif (FCFA)',
        'Total versé (FCFA)', 'Restant (FCFA)', 'Soldé',
        'Détails',
    ]
    for c in contribs_list:
        ds.append([
            str(c.membre),
            c.eglise.nom,
            c.eglise.groupe,
            c.eglise.region,
            str(c.type_contribution),
            c.date_contribution.strftime('%d/%m/%Y'),
            c.montant_objectif or '',
            c.total_verse,
            c.montant_restant if c.montant_restant is not None else '',
            'Oui' if c.est_solde else ('Non' if c.montant_objectif else '—'),
            c.details or '',
        ])
    total_objectif = sum(c.montant_objectif or 0 for c in contribs_list)
    total_verse = sum(c.total_verse for c in contribs_list)
    ds.append(['TOTAUX', '', '', '', '', '', total_objectif, total_verse, '', '', ''])

    resp = HttpResponse(
        ds.export('xlsx'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    resp['Content-Disposition'] = 'attachment; filename="contributions_export.xlsx"'
    return resp


def _contribs_pdf(contribs_list, label):
    total_objectif = sum(c.montant_objectif or 0 for c in contribs_list)
    total_verse = sum(c.total_verse for c in contribs_list)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="contributions_export.pdf"'
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("CONTRIBUTIONS — Export", styles['Title']),
        Paragraph(label, styles['Normal']),
        Spacer(1, 0.4*cm),
    ]

    header = ['Membre', 'Église', 'Groupe', 'Région', 'Type', 'Date',
              'Objectif', 'Versé', 'Soldé']
    data = [header]
    for c in contribs_list:
        data.append([
            str(c.membre)[:22],
            c.eglise.nom[:18],
            c.eglise.groupe[:13],
            c.eglise.region[:12],
            str(c.type_contribution)[:15],
            c.date_contribution.strftime('%d/%m/%Y'),
            f"{c.montant_objectif:,}" if c.montant_objectif else '—',
            f"{c.total_verse:,}",
            'Oui' if c.est_solde else ('Non' if c.montant_objectif else '—'),
        ])
    data.append([
        'TOTAUX', '', '', '', '', '',
        f"{total_objectif:,}", f"{total_verse:,}", '',
    ])

    col_widths = [3.8*cm, 3.8*cm, 2.8*cm, 2.5*cm, 2.8*cm, 2.2*cm,
                  2.5*cm, 2.5*cm, 1.2*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(_pdf_table_style())
    elements.append(table)
    doc.build(elements)
    resp.write(buf.getvalue())
    buf.close()
    return resp


# ─── EXPORT GCK MENSUEL ────────────────────────────────────────────────────────

def export_mensuel(bilans_soir, totaux_soir,
                   bilans_conf, totaux_conf,
                   bilans_impact, totaux_impact,
                   fmt, mois_label, annee, label_filtre):
    """Export de la vue mensuelle combinée GCK (3 sections)."""
    if fmt == 'XLS':
        return _mensuel_xlsx(bilans_soir, totaux_soir,
                             bilans_conf, totaux_conf,
                             bilans_impact, totaux_impact,
                             mois_label, annee)
    return _mensuel_pdf(bilans_soir, totaux_soir,
                        bilans_conf, totaux_conf,
                        bilans_impact, totaux_impact,
                        mois_label, annee, label_filtre)


def _mensuel_section_rows(bilans, totaux):
    rows = []
    for b in bilans:
        rows.append([
            b.date.strftime('%d/%m/%Y'),
            b.eglise.nom,
            b.eglise.groupe,
            b.eglise.region,
            b.adultes_hommes, b.adultes_femmes, b.total_adultes,
            b.jeunes_hommes, b.jeunes_femmes, b.total_jeunes,
            b.enfants, b.total_participants, b.nouveaux_convertis,
        ])
    rows.append([
        'TOTAUX', '', '', '',
        totaux['total_adultes_h'], totaux['total_adultes_f'], totaux['total_adultes'],
        totaux['total_jeunes_h'], totaux['total_jeunes_f'], totaux['total_jeunes'],
        totaux['total_enfants'], totaux['total_participants'], totaux['total_convertis'],
    ])
    return rows


def _mensuel_xlsx(bilans_soir, totaux_soir,
                  bilans_conf, totaux_conf,
                  bilans_impact, totaux_impact,
                  mois_label, annee):
    headers = ['Date', 'Église', 'Groupe', 'Région',
               'Adultes H', 'Adultes F', 'Total Adultes',
               'Jeunes H', 'Jeunes F', 'Total Jeunes',
               'Enfants', 'Total', 'Convertis']

    from tablib import Databook
    book = Databook()

    for label_section, bilans, totaux in [
        ('GCK Soir', bilans_soir, totaux_soir),
        ('Conférence', bilans_conf, totaux_conf),
        ('Académie Impact', bilans_impact, totaux_impact),
    ]:
        ds = Dataset(title=label_section[:31])
        ds.headers = headers
        for row in _mensuel_section_rows(bilans, totaux):
            ds.append(row)
        book.add_sheet(ds)

    resp = HttpResponse(
        book.export('xlsx'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    resp['Content-Disposition'] = f'attachment; filename="GCK_{mois_label}_{annee}.xlsx"'
    return resp


def _mensuel_pdf(bilans_soir, totaux_soir,
                 bilans_conf, totaux_conf,
                 bilans_impact, totaux_impact,
                 mois_label, annee, label_filtre):
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="GCK_{mois_label}_{annee}.pdf"'
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"GCK — Vue Mensuelle : {mois_label} {annee}", styles['Title']),
        Paragraph(label_filtre or 'Toutes les données', styles['Normal']),
        Spacer(1, 0.4*cm),
    ]

    header1 = ['Date', 'Église', 'Groupe', 'Région',
               'Adultes', '', '', 'Jeunes', '', '', 'Enfants', 'Total', 'Convertis']
    header2 = ['', '', '', '', 'H', 'F', 'Tot.', 'H', 'F', 'Tot.', '', '', '']
    col_widths = [1.9*cm, 4.5*cm, 3.0*cm, 2.5*cm,
                  1.3*cm, 1.3*cm, 1.5*cm, 1.3*cm, 1.3*cm, 1.5*cm,
                  1.4*cm, 1.5*cm, 1.7*cm]

    section_styles = [
        ('GCK — Séances du Soir', '#212529', bilans_soir, totaux_soir),
        ('Conférence des Ministres', '#78350f', bilans_conf, totaux_conf),
        ("Académie d'Impact", '#7c3aed', bilans_impact, totaux_impact),
    ]

    for section_title, header_color, bilans, totaux in section_styles:
        elements.append(Paragraph(section_title, styles['Heading2']))
        elements.append(Spacer(1, 0.2*cm))
        data = [header1, header2]
        for b in bilans:
            data.append([
                b.date.strftime('%d/%m/%Y'), b.eglise.nom[:22],
                b.eglise.groupe[:15], b.eglise.region[:12],
                str(b.adultes_hommes), str(b.adultes_femmes), str(b.total_adultes),
                str(b.jeunes_hommes), str(b.jeunes_femmes), str(b.total_jeunes),
                str(b.enfants), str(b.total_participants), str(b.nouveaux_convertis),
            ])
        data.append([
            'TOTAUX', '', '', '',
            str(totaux['total_adultes_h']), str(totaux['total_adultes_f']), str(totaux['total_adultes']),
            str(totaux['total_jeunes_h']), str(totaux['total_jeunes_f']), str(totaux['total_jeunes']),
            str(totaux['total_enfants']), str(totaux['total_participants']), str(totaux['total_convertis']),
        ])

        table = Table(data, colWidths=col_widths, repeatRows=2)
        ts = _pdf_table_style(n_header_rows=2)
        ts.add('SPAN', (0, 0), (0, 1))
        ts.add('SPAN', (1, 0), (1, 1))
        ts.add('SPAN', (2, 0), (2, 1))
        ts.add('SPAN', (3, 0), (3, 1))
        ts.add('SPAN', (4, 0), (6, 0))
        ts.add('SPAN', (7, 0), (9, 0))
        ts.add('SPAN', (10, 0), (10, 1))
        ts.add('SPAN', (11, 0), (11, 1))
        ts.add('SPAN', (12, 0), (12, 1))
        ts.add('BACKGROUND', (0, 0), (-1, 1), colors.HexColor(header_color))
        ts.add('BACKGROUND', (4, 0), (6, 1), colors.HexColor('#1a3d6b'))
        ts.add('BACKGROUND', (7, 0), (9, 1), colors.HexColor('#4a235a'))
        table.setStyle(ts)
        elements.append(table)
        elements.append(Spacer(1, 0.6*cm))

    doc.build(elements)
    resp.write(buf.getvalue())
    buf.close()
    return resp
