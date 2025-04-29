# Reset Password
import streamlit as st
st.set_page_config(page_title="Reset Password | RateZap", layout="centered")
from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3
import hashlib
from datetime import datetime, timedelta

st.title("🔐 Reset Your Password")

# Get token from URL
token = st.query_params.get("token")

if not token:
    st.error("Invalid or missing token.")
    st.stop()

# Connect DB
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

# Validate token
c.execute("SELECT id, email, token_expiry FROM users WHERE reset_token = ?", (token,))
row = c.fetchone()

if not row:
    st.error("Invalid or expired reset link.")
    st.stop()

user_id, email, expiry = row

# Check if token expired
if expiry:
    expiry_dt = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiry_dt + timedelta(minutes=30):
        st.error("This reset link has expired. Please request a new one.")
        st.stop()

st.success(f"Resetting password for: {email}")

# Form to reset password
new_password = st.text_input("New Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")

if st.button("🔄 Update Password"):
    if new_password != confirm_password:
        st.error("Passwords do not match.")
    elif len(new_password) < 6:
        st.warning("Password must be at least 6 characters long.")
    else:
        hashed = hashlib.sha256(new_password.encode()).hexdigest()
        c.execute("""
            UPDATE users
            SET password = ?, reset_token = NULL, token_expiry = NULL
            WHERE id = ?
        """, (hashed, user_id))
        conn.commit()
        st.success("✅ Password updated successfully. You may now log in.")














