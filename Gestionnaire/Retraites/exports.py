from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tablib


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _totaux(retraites):
    t = dict(
        adultes_h=0, adultes_f=0, jeunes_h=0, jeunes_f=0,
        enfants=0, convertis=0, eglises=0, participants=0,
    )
    for r in retraites:
        t['adultes_h'] += r.adultes_h
        t['adultes_f'] += r.adultes_f
        t['jeunes_h'] += r.jeunes_h
        t['jeunes_f'] += r.jeunes_f
        t['enfants'] += r.enfants
        t['convertis'] += r.nouveaux_convertis
        t['eglises'] += r.nombre_eglises
        t['participants'] += r.total_participants
    return t


# ─── Export PDF ───────────────────────────────────────────────────────────────

def export_retraites_pdf(retraites, label):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                             leftMargin=1*cm, rightMargin=1*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Rapport Retraites — {label}", styles['Title']))
    story.append(Spacer(1, 0.4*cm))

    headers = ['Région', 'Ad.H', 'Ad.F', 'Tot.Ad',
               'Je.H', 'Je.F', 'Tot.Je',
               'Enf.', 'Total', 'Convertis', 'Églises']
    data = [headers]

    retraites_list = list(retraites)
    tot = _totaux(retraites_list)

    for r in retraites_list:
        data.append([
            r.region.name,
            str(r.adultes_h), str(r.adultes_f), str(r.total_adultes),
            str(r.jeunes_h), str(r.jeunes_f), str(r.total_jeunes),
            str(r.enfants), str(r.total_participants),
            str(r.nouveaux_convertis), str(r.nombre_eglises),
        ])

    # Ligne total
    data.append([
        'TOTAL TOGO',
        str(tot['adultes_h']), str(tot['adultes_f']),
        str(tot['adultes_h'] + tot['adultes_f']),
        str(tot['jeunes_h']), str(tot['jeunes_f']),
        str(tot['jeunes_h'] + tot['jeunes_f']),
        str(tot['enfants']), str(tot['participants']),
        str(tot['convertis']), str(tot['eglises']),
    ])

    col_widths = [4*cm, 1.4*cm, 1.4*cm, 1.6*cm,
                  1.4*cm, 1.4*cm, 1.6*cm,
                  1.4*cm, 1.6*cm, 1.8*cm, 1.8*cm]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a6496')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d9534f')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tbl)

    doc.build(story)
    buf.seek(0)
    filename = f"retraites_{label.replace(' ', '_').replace('—', '-')}.pdf"
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


# ─── Export Excel ─────────────────────────────────────────────────────────────

def export_retraites_excel(retraites, label):
    headers = ['Région', 'Type', 'Année',
               'Adultes H', 'Adultes F', 'Total Adultes',
               'Jeunes H', 'Jeunes F', 'Total Jeunes',
               'Enfants', 'Total Participants',
               'Nouveaux convertis', 'Nb. Églises',
               'Lieu', 'Thème', 'Notes']
    dataset = tablib.Dataset(headers=headers, title='Retraites')

    retraites_list = list(retraites)
    for r in retraites_list:
        dataset.append([
            r.region.name,
            r.get_type_retraite_display(),
            r.annee,
            r.adultes_h, r.adultes_f, r.total_adultes,
            r.jeunes_h, r.jeunes_f, r.total_jeunes,
            r.enfants, r.total_participants,
            r.nouveaux_convertis, r.nombre_eglises,
            r.lieu, r.theme, r.notes,
        ])

    tot = _totaux(retraites_list)
    dataset.append([
        'TOTAL', '', '',
        tot['adultes_h'], tot['adultes_f'], tot['adultes_h'] + tot['adultes_f'],
        tot['jeunes_h'], tot['jeunes_f'], tot['jeunes_h'] + tot['jeunes_f'],
        tot['enfants'], tot['participants'],
        tot['convertis'], tot['eglises'],
        '', '', '',
    ])

    filename = f"retraites_{label.replace(' ', '_').replace('—', '-')}.xlsx"
    resp = HttpResponse(
        dataset.xlsx,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp
