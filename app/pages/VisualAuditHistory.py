
import streamlit as st
import sqlite3
import json
import pandas as pd
from app.helpers.night_audit_pdf import generate_audit_pdf
from datetime import datetime
import streamlit as st
st.set_page_config(page_title="Visual Audit History", layout="wide")
import sqlite3
import json
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
from app.utils import hide_streamlit_ui
hide_streamlit_ui()
#=======================================✨RateZap=============================================
st.markdown("""
    <style>
    .logout-button {
        position: fixed;
        top: 17px;
        left: 65px;
        background-color: rgba(0, 0, 0, 0.1);  /* Semi-transparent black */
        color: Red;
        padding: 5px 12px;
        border: 0px solid rgba(255, 255, 255, 0.3);  /* Light border */
        border-radius: 6px;
        font-size: 20px;
        z-index: 10000;
        transition: background-color 0.3s ease;
    }

    </style>
""", unsafe_allow_html=True)
st.markdown(
    "<button class='logout-button' onclick='window.location.reload()'>✨RateZap</button>",
    unsafe_allow_html=True
)
#================================================================================================

# Step 1: Create a logout button normally
logout_col = st.columns([10, 1])  # 10 parts space, 1 part logout button

with logout_col[1]:
    if st.button("🔓 Logout", key="logout_top_right"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Step 2: Style ONLY this logout button
st.markdown("""
    <style>
    div[data-testid="stButton"][key="logout_top_right"] button {
        background-color: rgba(0, 0, 0, 0.25);
        color: white;
        padding: 8px 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        font-size: 16px;
        line-height: 1;
        transition: background-color 0.3s ease;
        margin-top: -55px;  /* Pull up closer to top */
        margin-right: 10px; /* Pull closer to right */
    }
    div[data-testid="stButton"][key="logout_top_right"] button:hover {
        background-color: rgba(255, 75, 75, 0.9);
        border-color: rgba(255, 75, 75, 1.0);
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)


# 🔥 Page Header (Center aligned, nice style)
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 40px;font-size: 36px; color: #39FF14;'>
         📄 Audit History
    </h1>
""", unsafe_allow_html=True)

# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home.py")
    st.stop()

# ➡️ Custom Top Navigation Bar
# Split layout into 7 equal columns
with st.container():
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6, nav_col7 = st.columns(7)

    button_style = """
        <style>
        div.stButton > button {
            width: 100%;
            height: 3rem;
            font-size: 1.0rem;
            margin: 4px;
            border-radius: 8px;
        }
        </style>
    """
    st.markdown(button_style, unsafe_allow_html=True)

    with nav_col1:
        if st.button("🏠 Dashboard"):
            st.switch_page("Dashboard.py")

    with nav_col2:
        if st.button("📄 Annual Rates"):
            st.switch_page("AnnualRates.py")

    with nav_col3:
        if st.button("🛏️ Night Audit"):
            st.switch_page("NightAudit.py")

    with nav_col4:
        if st.button("🕓 Audit History"):
            st.switch_page("VisualAuditHistory.py")

    with nav_col5:
        if st.button("📈 Rate Optimizer"):
            st.switch_page("RateOptimizer.py")

    with nav_col6:
        if st.button("🏢 Companies List"):
            st.switch_page("Companies.py")

    with nav_col7:
        if st.button("👤 My Profile"):
            st.switch_page("Profile.py")

st.markdown("---")  # Nice separator line


# 🔒 Require login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.stop()

st.title("📋 Night Audit History")

# DB path
user_id = st.session_state["user"]["id"]
db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

# Load audits
try:
    audits = []
    with sqlite3.connect(db_path, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM night_audit_history WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        audits = c.fetchall()
except sqlite3.OperationalError as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

if not audits:
    st.info("No night audit reports found yet.")
    st.stop()

for audit in audits:
    (
        audit_id, uid, date_field, occupancy, adr,
        summary_json, extra_json, room_json,
        hotel_name, created_at
    ) = audit

    # 🛠️ Correctly handle audit date and time
    audit_date = "Unknown"
    audit_time = "Unknown"

    try:
        if created_at:
            dt_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            audit_date = dt_obj.strftime("%Y-%m-%d")
            audit_time = dt_obj.strftime("%I:%M %p")
        else:
            dt_obj = datetime.strptime(date_field, "%Y-%m-%d")
            audit_date = dt_obj.strftime("%Y-%m-%d")
            audit_time = "N/A"
    except Exception:
        try:
            dt_obj = datetime.strptime(date_field, "%Y-%m-%d")
            audit_date = dt_obj.strftime("%Y-%m-%d")
            audit_time = "N/A"
        except:
            audit_date = "Unknown"
            audit_time = "Unknown"

    with st.expander(f"🗓️ {audit_date} | 🏨 {hotel_name} | ⏰ {audit_time}"):
        # Parse summary
        
        try:
            summary = json.loads(summary_json) if summary_json else {}
        except:
            summary = {}

        if summary:
            st.markdown("#### 📊 Summary")
            summary_table = pd.DataFrame.from_dict(summary, orient="index", columns=["Value"])
            st.table(summary_table)
        else:
            st.info("No summary available for this audit.")

        # Room Breakdown
        room_df = pd.DataFrame()
        if room_json:
            try:
                decoded = json.loads(room_json)
                if isinstance(decoded, list):
                    room_df = pd.DataFrame(decoded)
                elif isinstance(decoded, dict):
                    room_df = pd.DataFrame([decoded])
            except Exception as e:
                st.error(f"Failed to parse room breakdown: {e}")

        if not room_df.empty:
            st.markdown("#### 🛌️ Room Breakdown")
            st.dataframe(room_df, use_container_width=True)
        else:
            st.info("ℹ️ No room breakdown available for this audit.")

        # Extra Fields
        extra_df = pd.DataFrame()
        if extra_json:
            try:
                decoded = json.loads(extra_json)
                if isinstance(decoded, list):
                    extra_df = pd.DataFrame(decoded)
                elif isinstance(decoded, dict):
                    extra_df = pd.DataFrame([decoded])
            except Exception as e:
                st.warning(f"⚠️ Failed to parse extra fields: {e}")

        if not extra_df.empty:
            st.markdown("#### 📌 Extra Fields")
            st.dataframe(extra_df, use_container_width=True)
            
    
        # 🔧 Required variables before PDF generation/email
        summary_data = summary
        room_summary_df = room_df if not room_df.empty else pd.DataFrame()
        extra_fields_df = extra_df if not extra_df.empty else pd.DataFrame()
        user_email = st.session_state["user"]["email"]
        full_name = st.session_state["user"].get("full_name", "User")


        # Download PDF
                # 📄 Action Buttons: Download | Email | Refresh
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.download_button(
                label="📥 Download PDF",
                data=generate_audit_pdf(hotel_name, summary_data, room_summary_df, extra_fields_df),
                file_name=f"NightAudit_{audit_date}.pdf",
                mime="application/pdf",
                key=f"download_{audit_id}"
            )

        with col2:
            if st.button(f"📧 Email Audit {audit_date}", key=f"email_{audit_id}"):
                 with st.spinner("📧 Sending email..."):
                    try:
                        pdf_bytes = generate_audit_pdf(hotel_name, summary_data, room_summary_df, extra_fields_df)
                        
                        message = MIMEMultipart()
                        message["From"] = EMAIL_ADDRESS
                        message["To"] = user_email
                        message["Subject"] = f"✅ Night Audit Report — {hotel_name} ({audit_date})"

                        body = MIMEText(f"""
                        Hi {full_name},

                        Please find attached the night audit report for {hotel_name} dated {audit_date}.

                        Regards,
                        RateZap Team
                        """, "plain")
                        message.attach(body)

                        part = MIMEApplication(pdf_bytes, Name=f"NightAudit_{audit_date}.pdf")
                        part['Content-Disposition'] = f'attachment; filename="NightAudit_{audit_date}.pdf"'
                        message.attach(part)

                        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                            server.starttls()
                            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

                        st.success(f"📧 Audit emailed successfully for {audit_date}!")
                    except Exception as e:
                        st.error(f"❌ Failed to send email: {e}")

        with col3:
            if st.button(f"🔁 Refresh Chart {audit_date}", key=f"refresh_{audit_id}"):
                st.session_state["audit_updated"] = True
                st.rerun()


        

        st.markdown("---")
