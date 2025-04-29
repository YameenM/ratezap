import streamlit as st
# Page config
st.set_page_config(page_title="Daily Email Preview | RateZap", layout="centered")
from utils import hide_streamlit_ui
hide_streamlit_ui()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from datetime import datetime

# Require login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to view this page.")
    st.stop()

user = st.session_state["user"]
user_id = user.get("id")
full_name = user.get("full_name", "Guest")
email = user.get("email")

conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

# Latest suggestion
c.execute("""
    SELECT timestamp, occupancy, competitor_rate, local_event, day_type,
           suggested_rate, currency, hotel_name
    FROM rate_history
    WHERE user_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
""", (user_id,))
row = c.fetchone()

if not row:
    st.info("No rate suggestion found. Generate one in the dashboard.")
    st.stop()

ts, occ, comp, event, day, rate, currency, hotel_name = row

# Location
c.execute("SELECT city, country FROM user_settings WHERE user_id = ?", (user_id,))
loc = c.fetchone()
city, country = loc if loc else ("", "")

confidence = "High" if occ > 80 else "Medium" if occ > 60 else "Low"
reason = []
if occ > 80: reason.append("High occupancy")
if event == "Yes": reason.append("Local event")
if day == "Weekend": reason.append("Weekend boost")
reason_text = ", ".join(reason) if reason else "No strong factors."

# HTML preview
html = f'''
<div style="font-family:sans-serif;background:#f8f9fa;padding:20px;border-radius:12px;color:#222;">
  <h2>📨 Daily Rate Reminder</h2>
  <p>Hi <strong>{full_name}</strong>,</p>
  <p>Here’s your recommended nightly rate for <strong>{hotel_name}</strong> in <em>{city}, {country}</em>:</p>
  <h3 style="color:#2e7d32">💰 {currency} {rate:.2f}</h3>
  <p><strong>Confidence:</strong> {confidence}</p>
  <p><strong>Why:</strong> {reason_text}</p>
  <p style="margin-top:20px;color:#666;">– The RateZap Team</p>
</div>
'''

st.markdown("### 📬 Preview Email:")
st.components.v1.html(html, height=300, scrolling=True)

# Optional: Send test email to self
if st.button("📤 Send to My Email"):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RateZap - Daily Rate Suggestion ({datetime.now().strftime('%b %d')})"
        msg["From"] = "ratezap@example.com"  # Optional: Replace with your sender
        msg["To"] = email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("localhost") as server:  # For test only; use real SMTP if needed
            server.sendmail(msg["From"], msg["To"], msg.as_string())

        st.success(f"✅ Sent to {email}")
    except Exception as e:
        st.error(f"❌ Failed: {e}")