import streamlit as st
st.set_page_config(page_title="Send Daily Emails | RateZap", layout="wide")
from app.utils import hide_streamlit_ui

hide_streamlit_ui()

# 🚫 Restrict to admin only
if "user" not in st.session_state or st.session_state.user.get("email") != "admin@ratezap.com":
    st.warning("⚠️ You are not authorized to view this page.")
    st.markdown("[🔐 Click here to return to login](./)")
    st.markdown('<meta http-equiv="refresh" content="2; url=/">', unsafe_allow_html=True)
    st.stop()

import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# 🔧 SMTP Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "myabran@gmail.com"  # Replace
APP_PASSWORD = "emof wfnc gztj xcfx"  # Replace

st.title("📨 Send Daily Rate Emails to All Users")

# Connect DB
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

# Latest rate suggestion
c.execute("""
    SELECT user_id, timestamp, occupancy, competitor_rate, local_event, day_type,
           suggested_rate, currency, hotel_name
    FROM rate_history
    ORDER BY timestamp DESC
    LIMIT 1
""")
latest = c.fetchone()
if not latest:
    st.warning("⚠️ No rate suggestions found. Generate one first.")
    st.stop()

user_id, ts, occ, comp, event, day, rate, currency, hotel_name = latest

# Hotel location info
c.execute("SELECT city, country FROM user_settings WHERE user_id = ?", (user_id,))
loc = c.fetchone()
city, country = loc if loc else ("", "")

# Users list (excluding admin)
c.execute("SELECT id, full_name, email FROM users WHERE email != 'admin@ratezap.com'")
users = c.fetchall()

if st.button("📤 Send Now"):
    for uid, name, email in users:
        confidence = "High" if occ > 80 else "Medium" if occ > 60 else "Low"
        reason = []
        if occ > 80: reason.append("High occupancy")
        if event == "Yes": reason.append("Local event")
        if day == "Weekend": reason.append("Weekend boost")
        reason_text = ", ".join(reason) or "No strong factors."

        # Compose email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RateZap Daily Rate - {datetime.now().strftime('%b %d')}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = email

        html = f'''
        <div style="font-family:sans-serif;background:#f8f9fa;padding:20px;border-radius:12px;color:#222;">
          <h2>📨 Daily Rate Suggestion</h2>
          <p>Hi <strong>{name}</strong>,</p>
          <p>Here’s your recommended nightly rate for <strong>{hotel_name}</strong> in <em>{city}, {country}</em>:</p>
          <h3 style="color:#2e7d32">💰 {currency}{rate:.2f}</h3>
          <p><strong>Confidence:</strong> {confidence}</p>
          <p><strong>Why:</strong> {reason_text}</p>
          <p style="margin-top:20px;color:#666;">– The RateZap Team</p>
        </div>
        '''
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.sendmail(SENDER_EMAIL, email, msg.as_string())
            st.success(f"✅ Email sent to {email}")
        except Exception as e:
            st.error(f"❌ Failed for {email}: {e}")

conn.close()
