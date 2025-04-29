from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import pandas as pd
from datetime import datetime
from helpers.utils import hide_streamlit_ui
hide_streamlit_ui()

def generate_pdf(company_name, timestamp, occupancy, adr, summary_data, room_df=None, extra_df=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=12, leading=14, spaceAfter=8, textColor=colors.HexColor("#2b6cb0")))

    # Title
    story.append(Paragraph("<b>Night Audit Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # Header Info
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles["Normal"]))
    story.append(Paragraph(f"— {timestamp}", styles["Normal"]))
    story.append(Paragraph(f"<font color='gray'>■ {company_name} &nbsp;&nbsp;&nbsp; ■ Occupancy: {occupancy}% &nbsp;&nbsp;&nbsp; ■ ADR: {adr}</font>", styles["Normal"]))
    story.append(Spacer(1, 16))

    # Summary Table
    story.append(Paragraph("<b>■ Summary</b>", styles["SectionHeader"]))
    summary_table = [
        ["Total Rooms", summary_data.get("Total_Rooms", 0)],
        ["Occupied", summary_data.get("Occupied", 0)],
        ["Vacant", summary_data.get("Vacant", 0)],
        ["Average Rate", f"{summary_data.get('symbol', '')}{float(summary_data.get('Average_Rate', 0)):.2f}"],
        ["ADR", f"{summary_data.get('symbol', '')}{float(summary_data.get('ADR', 0)):.2f}"],
        ["Revenue", f"{summary_data.get('symbol', '')}{float(summary_data.get('Revenue', 0)):.2f}"],
    ]
    summary_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ])
    summary_table_obj = Table(summary_table, hAlign='LEFT')
    summary_table_obj.setStyle(summary_style)
    story.append(summary_table_obj)
    story.append(Spacer(1, 16))

    # Room Breakdown Table
    if room_df is not None and not room_df.empty:
        # Ensure types are correct
        for col in ["Total_Rooms", "Occupied_Rooms", "Average_Rate"]:
            if col in room_df.columns:
                room_df[col] = pd.to_numeric(room_df[col], errors="coerce")

        story.append(Paragraph("<b>■ Room Type Breakdown</b>", styles["SectionHeader"]))
        room_data = [room_df.columns.tolist()] + room_df.fillna("-").values.tolist()
        room_table = Table(room_data, hAlign='LEFT')
        room_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        story.append(room_table)
        story.append(Spacer(1, 16))

    # Extra Fields
    if extra_df is not None and not extra_df.empty:
        story.append(Paragraph("<b>■ Additional Details</b>", styles["SectionHeader"]))
        extra_data = [extra_df.columns.tolist()] + extra_df.fillna("-").values.tolist()
        extra_table = Table(extra_data, hAlign='LEFT')
        extra_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        story.append(extra_table)
        story.append(Spacer(1, 16))

    # Footer
    story.append(Spacer(1, 12))
    story.append(Paragraph("<font size=8 color=gray>Generated via RateZap | ratezap.ai</font>", styles["Normal"]))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf