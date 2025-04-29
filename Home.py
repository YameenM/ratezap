# Home.py
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
from app.utils import hide_streamlit_ui

st.set_page_config(page_title="Home | RateZap", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()

# Hide sidebar for unauthenticated users
if "user" not in st.session_state:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

# Toggle between register/login
if "is_register" not in st.session_state:
    st.session_state["is_register"] = False

# DB connection
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

# Utilities
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(email, password):
    hashed = hash_password(password)
    c.execute("SELECT id, full_name, email, subscription_status, trial_start FROM users WHERE email = ? AND password = ?", (email, hashed))
    return c.fetchone()

# 2-Tone Layout
left, right = st.columns([1, 1])
with left:
    # Welcome box
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1f2937, #3b82f6); padding: 40px; border-radius: 16px; color: white;'>
        <h1 style="font-size: 40px;">👋 Welcome to <span style="color:#facc15;">RateZap</span></h1>
        <p style="font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
            Smarter hotel pricing starts here.
        </p>
        <ul style='font-size: 16px; margin-bottom: 30px; line-height: 1.8;'>
            <li>📊 Dynamic rate suggestions</li>
            <li>📅 Night audit + annual planner</li>
            <li>📬 Email alerts + forecast</li>
            <li>🔍 Rate Optimizer & Revenue Projection</li>
            <li>🏨 Built for independent hotels</li>
        </ul>
        <h3 style='margin-bottom:8px;'> ✨ <span style='color:#10b981;'>FREE for 7 Days</span> </h3>
        <form action="/Pricing">
            <button style='margin-top:5px; padding: 10px 20px; font-size: 20px; background-color: #2563eb; color: white; border: 1px solid #facc15; border-radius: 18px; cursor: pointer;'>
                💼 View Plans
            </button>
        </form>
        
    </div>
    """, unsafe_allow_html=True)


with right:
    st.markdown("#### 🔐 Access Your Account")

    is_register = st.toggle("Create a new account", value=st.session_state["is_register"], key="register_toggle")
    st.session_state["is_register"] = is_register

    if is_register:
        st.markdown("#### 📝 Register")
        full_name = st.text_input("Full Name", key="reg_full_name")
        email = st.text_input("Email", key="reg_email").strip().lower()
        password = st.text_input("Password", type="password", key="reg_password")

        if st.button("🚀 Register", key="register_btn"):
            if not all([full_name.strip(), email.strip(), password.strip()]):
                st.warning("⚠️ Please fill in all fields.")
            elif len(password) < 6:
                st.warning("🔑 Password must be at least 6 characters.")
            else:
                try:
                    hashed_pw = hash_password(password)
                    trial_start_date = datetime.now().strftime("%Y-%m-%d")

                    # 🔥 Check if this is the first ever user
                    c.execute("SELECT COUNT(*) FROM users")
                    user_count = c.fetchone()[0]

                    if user_count == 0:
                        subscription_status = "admin"
                    else:
                        subscription_status = "trial"

                    c.execute('''
                        INSERT INTO users (full_name, email, password, subscription_status, trial_start)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (full_name, email, hashed_pw, subscription_status, trial_start_date))

                    
                    conn.commit()
                    user_id = c.lastrowid
                    st.session_state["user"] = {"id": user_id, "full_name": full_name, "email": email, "status": "trial"}

                    # Preload settings
                    c.execute("SELECT prop_type, prop_name, city, country, currency FROM user_settings WHERE user_id = ?", (user_id,))
                    row = c.fetchone()
                    st.session_state["custom_data"] = {
                        "prop_type": row[0] if row else "",
                        "prop_name": row[1] if row else "",
                        "city": row[2] if row else "",
                        "country": row[3] if row else "",
                        "currency": row[4] if row else "$"
                    }

                    st.toast("✅ Registered! Redirecting...")
                    st.switch_page("Dashboard")

                except sqlite3.IntegrityError:
                    st.error("❌ This email is already registered.")

    else:
        st.markdown("#### 🔑 Login")
        login_email = st.text_input("Email", key="login_email_input").strip().lower()
        login_password = st.text_input("Password", type="password", key="login_password_input")

        if st.button("➡️ Login", key="login_btn"):
            user = check_credentials(login_email, login_password)
            if user:
                user_id, full_name, email, status, trial_start = user

                # Trial expiry check
                if status == "trial" and trial_start:
                    trial_date = datetime.strptime(trial_start, "%Y-%m-%d")
                    if datetime.now() > trial_date + timedelta(days=7):
                        status = "expired"
                        c.execute("UPDATE users SET subscription_status = ? WHERE id = ?", ("expired", user_id))
                        conn.commit()

                if status == "expired":
                    st.warning("🚫 Your free trial has expired. Please Upfrade to Continue...")
                    st.switch_page("UpgradePrompt")
                    st.stop()


                st.session_state["user"] = {
                    "id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "status": status,
                    "trial_start": trial_start
                }

                # Preload settings
                c.execute("SELECT prop_type, prop_name, city, country, currency FROM user_settings WHERE user_id = ?", (user_id,))
                row = c.fetchone()
                st.session_state["custom_data"] = {
                    "prop_type": row[0] if row else "",
                    "prop_name": row[1] if row else "",
                    "city": row[2] if row else "",
                    "country": row[3] if row else "",
                    "currency": row[4] if row else "$"
                }
                
                st.toast(f"✅ Welcome, {full_name}!")
                
                if status == "admin":
                    st.switch_page("Admin")
                else:
                    st.switch_page("Dashboard")

            else:
                st.error("❌ Invalid email or password.")
