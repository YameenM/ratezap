# pages/Admin.py

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import os
import shutil

st.set_page_config(page_title="Admin | RateZap", layout="wide", initial_sidebar_state="collapsed")

# 🔐 Admin Access Control
user = st.session_state.get("user", {})
email = user.get("email", "").lower()
if email != "admin@ratezap.com":
    st.warning("⚠️ You are not authorized to view this page.")
    st.markdown("[🔐 Click here if you're not redirected](./)")
    st.markdown('<meta http-equiv="refresh" content="2; url=/" />', unsafe_allow_html=True)
    st.stop()

# 📦 DB
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

# UI
st.title("🛠️ Admin Panel")
if st.button("🔓 Logout"):
    st.session_state.clear()
    st.rerun()
st.markdown("---")

# 📊 Insights
c.execute("SELECT COUNT(*) FROM users WHERE email != 'admin@ratezap.com'")
total_users = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'expired'")
expired_trials = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'trial'")
active_trials = c.fetchone()[0]

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total Users", total_users)
col2.metric("🧭 Active Trials", active_trials)
col3.metric("⌛ Expired Trials", expired_trials)

# 📤 Mass Email Latest Rate
if st.button("📬 Send Latest Rate to All Users"):
    c.execute("SELECT * FROM users WHERE email != 'admin@ratezap.com'")
    all_users = c.fetchall()

    c.execute("""
        SELECT timestamp, occupancy, competitor_rate, local_event, day_type,
               suggested_rate, currency, hotel_type
        FROM rate_history
        ORDER BY timestamp DESC LIMIT 1
    """)
    latest = c.fetchone()

    if not latest:
        st.warning("⚠️ No rate suggestion available.")
    else:
        for user in all_users:
            uid, full_name, _, city, country, phone, email, *_ = user
            ts, occ, comp, event, day, rate, currency, hotel_type = latest
            confidence = "High" if occ > 80 else "Medium" if occ > 60 else "Low"
            reason = []
            if occ > 80: reason.append("High occupancy")
            if event == "Yes": reason.append("Local event")
            if day == "Weekend": reason.append("Weekend boost")
            reason_text = ", ".join(reason) or "No strong factors"

            html = f'''
            <div style="font-family:sans-serif;background:#f8f9fa;padding:20px;border-radius:12px;color:#222;">
              <h2>📨 Daily Rate Suggestion</h2>
              <p>Hi <strong>{full_name}</strong>,</p>
              <p>Here’s your recommended nightly rate:</p>
              <h3 style="color:#2e7d32">💰 {currency}{rate:.2f}</h3>
              <p><strong>Confidence:</strong> {confidence}</p>
              <p><strong>Why:</strong> {reason_text}</p>
              <p style="margin-top:20px;color:#666;">– RateZap Team</p>
            </div>
            '''

            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"RateZap - {datetime.now().strftime('%b %d')}"
                msg["From"] = "myabran@gmail.com"
                msg["To"] = email
                msg.attach(MIMEText(html, "html"))
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login("myabran@gmail.com", "emof wfnc gztj xcfx")
                    server.sendmail(msg["From"], msg["To"], msg.as_string())
                st.success(f"✅ Sent to {email}")
            except Exception as e:
                st.error(f"❌ Failed for {email}: {e}")

# 🔄 Reset Email Sender
def send_reset_email(to_email, full_name, token):
    try:
        link = f"https://your-domain.com/ResetPassword?token={token}"
        html = f"""
        <div style='font-family:sans-serif;padding:20px;color:#333;'>
            <h2>🔐 Password Reset</h2>
            <p>Hello {full_name},</p>
            <p>Click the link to reset your RateZap password:</p>
            <p><a href='{link}' target='_blank'>{link}</a></p>
            <p>This link expires in 30 minutes.</p>
        </div>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "RateZap Password Reset"
        msg["From"] = "ratezap@example.com"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("myabran@gmail.com", "emof wfnc gztj xcfx")
            server.sendmail(msg["From"], msg["To"], msg.as_string())
        return True
    except Exception as e:
        st.error(f"❌ Email Error: {e}")
        return False

# 🧾 User List
st.markdown("### 👥 Manage Users")
c.execute("SELECT id, full_name, hotel_name, city, country, phone, email, subscription_status FROM users WHERE email != 'admin@ratezap.com'")
users = c.fetchall()

for uid, name, hotel, city, country, phone, email, status in users:
    badge = "🟢 Trial" if status == "trial" else "🔴 Expired" if status == "expired" else "🟡 Pro"
    with st.expander(f"{name} ({badge}) - {email}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📍 {hotel}, {city}, {country}")
            st.write(f"📞 {phone}")
            st.write(f"🪪 Status: **{status.capitalize()}**")

        with col2:
            if st.button("🔒 Send Reset Link", key=f"reset_{uid}"):
                token = secrets.token_urlsafe(32)
                expiry = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("UPDATE users SET reset_token = ?, token_expiry = ? WHERE id = ?", (token, expiry, uid))
                conn.commit()
                if send_reset_email(email, name, token):
                    st.success("✅ Reset link sent.")
            if st.button("⭐ Grant Pro Access", key=f"pro_{uid}"):
                c.execute("UPDATE users SET subscription_status = ? WHERE id = ?", ("pro", uid))
                conn.commit()
                st.success("✅ User upgraded to Pro.")
                st.rerun()
            if st.button("🗑️ Deactivate (soon)", key=f"deactivate_{uid}"):
                st.warning("Deactivation logic coming soon.")
                
                
# ----------------------------------
# 🛡 Safe Reset Function
# ----------------------------------
def safe_reset_night_audit_history():
    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"
    backup_path = f"{db_path.replace('.db', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    try:
        # Backup DB first
        shutil.copy(db_path, backup_path)
        st.success(f"✅ Backup created: {backup_path}")

        # Delete records
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM night_audit_history;")
        conn.commit()
        conn.close()

        st.success("✅ Night Audit Records Reset Successfully!")
    except Exception as e:
        st.error(f"❌ Failed to reset audits: {e}")

# ----------------------------------
# 🚀 Admin Panel Button
# ----------------------------------
st.markdown("### 🛠️ Developer Tools (Admin Only)")

if st.button("⚡ Reset Night Audit Records", use_container_width=True):
    with st.spinner("Resetting night audit data..."):
        safe_reset_night_audit_history()
        
        
# ----------------------------------
# 🗑️ Delete Specific Night Audit
# ----------------------------------
def delete_specific_night_audit(selected_date, selected_hotel):
    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM night_audit_history
            WHERE audit_date = ? AND hotel_name = ?
        ''', (selected_date, selected_hotel))

        conn.commit()
        conn.close()

        st.success(f"✅ Successfully deleted audit for {selected_hotel} on {selected_date}.")
    except Exception as e:
        st.error(f"❌ Failed to delete audit: {e}")

# ----------------------------------
# 🚀 Delete Specific Audit Form
# ----------------------------------
st.markdown("### 🧹 Delete a Specific Night Audit")

# Fetch available audits
try:
    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT audit_date, hotel_name FROM night_audit_history ORDER BY audit_date DESC")
    available_audits = cursor.fetchall()
    conn.close()

    if available_audits:
        options = [f"{audit_date} | {hotel}" for audit_date, hotel in available_audits]
        selected_option = st.selectbox("📅 Select Audit to Delete", options)

        if selected_option:
            selected_date, selected_hotel = selected_option.split(" | ")
            selected_hotel = selected_hotel.strip()

            if st.button("🗑️ Confirm Delete Audit", use_container_width=True):
                with st.spinner("Deleting selected audit..."):
                    delete_specific_night_audit(selected_date, selected_hotel)
    else:
        st.info("ℹ️ No night audits available to delete.")

except Exception as e:
    st.error(f"❌ Could not load audits: {e}")
