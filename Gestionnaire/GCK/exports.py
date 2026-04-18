"""Export PDF et Excel de la vue mensuelle GCK (Soir + Conférence + Impact)."""
from django.http import HttpResponse
from io import BytesIO


# ─── helpers ──────────────────────────────────────────────────────────────────

COLS = ['Église', 'Groupe', 'Région', 'Date', 'A.H', 'A.F', 'J.H', 'J.F', 'Enf.', 'Convertis', 'Total']

def _rows(bilans):
    rows = []
    for b in bilans:
        rows.append([
            b.eglise.nom,
            b.eglise.groupe,
            b.eglise.region,
            b.date.strftime('%d/%m/%Y'),
            b.adultes_hommes,
            b.adultes_femmes,
            b.jeunes_hommes,
            b.jeunes_femmes,
            b.enfants,
            b.nouveaux_convertis,
            b.total_participants,
        ])
    return rows


def _totaux_row(t):
    return [
        'TOTAL', '', '', '',
        t['total_adultes_h'],
        t['total_adultes_f'],
        t['total_jeunes_h'],
        t['total_jeunes_f'],
        t['total_enfants'],
        t['total_convertis'],
        t['total_participants'],
    ]


# ─── Excel ────────────────────────────────────────────────────────────────────

def _excel(bilans_soir, totaux_soir, bilans_conf, totaux_conf,
           bilans_impact, totaux_impact, mois_label, annee, label_filtre):
    import tablib

    wb = tablib.Databook()

    sections = [
        ('Séances du Soir', bilans_soir, totaux_soir),
        ('Conférence Ministres', bilans_conf, totaux_conf),
        ('Académie Impact', bilans_impact, totaux_impact),
    ]

    for titre, bilans, totaux in sections:
        ds = tablib.Dataset(title=titre[:31])
        ds.headers = COLS
        for row in _rows(bilans):
            ds.append(row)
        ds.append(_totaux_row(totaux))
        wb.add_sheet(ds)

    buf = BytesIO()
    buf.write(wb.xlsx)
    buf.seek(0)
    filename = f"GCK_{mois_label}_{annee}.xlsx".replace(' ', '_')
    response = HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─── PDF ──────────────────────────────────────────────────────────────────────

def _pdf(bilans_soir, totaux_soir, bilans_conf, totaux_conf,
         bilans_impact, totaux_impact, mois_label, annee, label_filtre):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=13)
    sub_style = ParagraphStyle('sub', parent=styles['Heading2'], fontSize=10, spaceAfter=4)

    COL_WIDTHS = [4.5*cm, 3*cm, 2.8*cm, 2.2*cm,
                  1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.8*cm, 1.4*cm]

    HDR_COLOR = colors.HexColor('#1e3a5f')
    TOT_COLOR = colors.HexColor('#374151')
    ALT_COLOR = colors.HexColor('#f3f4f6')

    def make_section_table(bilans, totaux):
        data = [COLS]
        for i, row in enumerate(_rows(bilans)):
            data.append(row)
        data.append(_totaux_row(totaux))

        t = Table(data, colWidths=COL_WIDTHS, repeatRows=1)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), HDR_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('ALIGN', (4, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, ALT_COLOR]),
            ('BACKGROUND', (0, -1), (-1, -1), TOT_COLOR),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d1d5db')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        t.setStyle(TableStyle(style))
        return t

    story = [
        Paragraph(f"Rapport GCK Mensuel — {label_filtre}", title_style),
        Spacer(1, 0.3*cm),
    ]

    sections = [
        ('Séances du Soir (GCK)', bilans_soir, totaux_soir),
        ('Conférence des Ministres', bilans_conf, totaux_conf),
        ('Académie d\'Impact', bilans_impact, totaux_impact),
    ]

    for titre, bilans, totaux in sections:
        story.append(Paragraph(titre, sub_style))
        story.append(make_section_table(bilans, totaux))
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    buf.seek(0)
    filename = f"GCK_{mois_label}_{annee}.pdf".replace(' ', '_')
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def export_mensuel(bilans_soir, totaux_soir, bilans_conf, totaux_conf,
                   bilans_impact, totaux_impact, fmt, mois_label, annee, label_filtre):
    if fmt == 'XLS':
        return _excel(bilans_soir, totaux_soir, bilans_conf, totaux_conf,
                      bilans_impact, totaux_impact, mois_label, annee, label_filtre)
    return _pdf(bilans_soir, totaux_soir, bilans_conf, totaux_conf,
                bilans_impact, totaux_impact, mois_label, annee, label_filtre)
