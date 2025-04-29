import streamlit as st
import pandas as pd
import sqlite3
import os
import time
import json
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import altair as alt
from utils import hide_streamlit_ui
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

hide_streamlit_ui()

# ----------------------------------
# ✅ Helper: DB Connection
# ----------------------------------
def get_db_connection():
    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"
    return sqlite3.connect(db_path, check_same_thread=False)

# ----------------------------------
# ✅ Helper: Convert to JSON Safe
# ----------------------------------
def convert_to_serializable(data):
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return {}

# ----------------------------------
# ✅ Save Audit Summary into DB
# ----------------------------------
def save_audit_summary(user_id, audit_date, occupancy_pct, adr, summary_dict, extra_data=None, hotel_name="Hotel", room_breakdown_json=None):
    summary_json = json.dumps(summary_dict)
    extra_json = json.dumps(extra_data) if extra_data else None

    MAX_RETRIES = 5

    for attempt in range(MAX_RETRIES):
        try:
            with get_db_connection() as conn:
                c = conn.cursor()

                c.execute('''
                    INSERT INTO night_audit_history (
                        user_id, date, occupancy, adr,
                        summary_data, extra_fields, hotel_name, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, audit_date, occupancy_pct, adr,
                    summary_json, extra_json, hotel_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))


                last_id = c.lastrowid

                if room_breakdown_json:
                    c.execute("UPDATE night_audit_history SET room_breakdown = ? WHERE id = ?", (room_breakdown_json, last_id))

                conn.commit()
            break  # ✅ success
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(0.5)
            else:
                raise e
    else:
        raise Exception("❌ Database is locked after multiple retries. Please try again later.")


# ----------------------------------
# ✅ Helper: Common Table Style
# ----------------------------------
def base_table_style(header_bg=colors.lightgrey, row_bg=colors.beige):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey)
    ])

# ----------------------------------
# ✅ Generate Audit PDF
# ----------------------------------
def generate_audit_pdf(hotel_name, summary_data, room_df, extra_df=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=40, bottomMargin=40, leftMargin=40, rightMargin=40)
    elements = []
    styles = getSampleStyleSheet()

    # Styles
    title_style = ParagraphStyle('TitleCustom', parent=styles['Title'], fontSize=20, spaceAfter=12)
    heading_style = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#2b6cb0"), spaceBefore=10, spaceAfter=6)
    footer_style = ParagraphStyle('FooterCustom', fontSize=8, textColor=colors.grey, alignment=1)
    timestamp_style = ParagraphStyle(name="TopRightTimestamp", parent=styles["Normal"], fontSize=10, textColor=colors.grey, alignment=2)

    # Header
    elements.append(Paragraph("Night Audit Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", timestamp_style))
    elements.append(Paragraph(f"{hotel_name}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Summary Table
    elements.append(Paragraph("■ Summary", heading_style))
    summary_table = Table([
        ["Total Rooms", summary_data["Total_Rooms"]],
        ["Occupied Rooms", summary_data["Occupied"]],
        ["Vacant Rooms", summary_data["Vacant"]],
        ["Average Rate", f"{summary_data['symbol']}{summary_data['Average_Rate']:.2f}"],
        ["ADR", f"{summary_data['symbol']}{summary_data['ADR']:.2f}"],
        ["Revenue", f"{summary_data['symbol']}{summary_data['Revenue']:.2f}"]
    ], hAlign='LEFT')
    summary_table.setStyle(base_table_style())
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # Room Breakdown Table
    if room_df is not None and not room_df.empty:
        elements.append(Paragraph("■ Room Type Breakdown", heading_style))
        room_data = [["Room Type", "Total Rooms", "Occupied", "Avg Rate"]]
        for _, row in room_df.iterrows():
            try:
                room_data.append([
                    row["Room Type"],
                    int(row["Total_Rooms"]),
                    int(row["Occupied_Rooms"]),
                    f"{summary_data['symbol']}{row['Average_Rate']:.2f}"
                ])
            except Exception:
                continue
        table = Table(room_data, hAlign="LEFT", colWidths=[130, 80, 80, 100])
        table.setStyle(base_table_style(header_bg=colors.HexColor("#2b6cb0")))
        elements.append(table)
        elements.append(Spacer(1, 20))

    # Extra Fields Table
    if extra_df is not None and not extra_df.empty:
        elements.append(Paragraph("■ Additional Fields", heading_style))
        preview_data = [extra_df.columns.tolist()] + extra_df.fillna("").astype(str).values.tolist()
        preview_table = Table(preview_data, hAlign="LEFT")
        preview_table.setStyle(base_table_style())
        elements.append(preview_table)

    # Footer
    elements.append(Spacer(1, 36))
    elements.append(Paragraph("Generated via RateZap | ratezap.ai", footer_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ----------------------------------
# ✅ Render Occupancy & ADR Trend Chart
# ----------------------------------
def render_trend_chart(user_id, db_path=None):
    st.markdown("##### 📈📉 Occupancy & ADR Trend (Last 7 Audits)")
    try:
        if not db_path:
            db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

        conn = sqlite3.connect(db_path)
        query = """
            SELECT date, occupancy, adr
            FROM night_audit_history
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 7
        """
        trend_df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()

        trend_df["date"] = pd.to_datetime(trend_df["date"])
        trend_df = trend_df.sort_values("date")

        base = alt.Chart(trend_df).encode(x='date:T')

        line1 = base.mark_line(color='steelblue').encode(
            y=alt.Y('occupancy:Q', axis=alt.Axis(title='Occupancy %'))
        )

        line2 = base.mark_line(color='orange').encode(
            y=alt.Y('adr:Q', axis=alt.Axis(title='ADR'), scale=alt.Scale(zero=False))
        )

        chart = alt.layer(line1, line2).resolve_scale(y='independent').properties(
            title="💤✍️ Last 7 Nights Audits – Occupancy ﹪ 🆚 ADR",
            width=700,
            height=320
        )

        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Could not generate trend chart: {e}")
        

# Send Night Audit Email. 

def send_night_audit_email(user_email, full_name, hotel_name, total_rooms, occupied, vacant, adr, symbol):
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    smtp_server = "smtp.example.com"
    smtp_port = 587

    subject = f"✅ Night Audit Uploaded Successfully — {hotel_name}"

    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    adr_formatted = f"{adr:,.2f}"

    html = f"""
    <p>Hi {full_name},</p>

    <p>Your Night Audit report for <strong>{hotel_name}</strong> has been uploaded successfully on <strong>{upload_date}</strong>.</p>

    <table border="1" cellspacing="0" cellpadding="8">
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Total Rooms</td><td>{total_rooms}</td></tr>
    <tr><td>Occupied Rooms</td><td>{occupied}</td></tr>
    <tr><td>Vacant Rooms</td><td>{vacant}</td></tr>
    <tr><td>Average Rate (ADR)</td><td>{symbol}{adr_formatted}</td></tr>
    </table>

    <p>📥 You can view detailed reports inside your RateZap dashboard.</p>

    <p>Thanks,<br><strong>RateZap Team</strong></p>
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

