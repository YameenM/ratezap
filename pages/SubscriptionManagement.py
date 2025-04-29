from app.utils import hide_streamlit_ui
hide_streamlit_ui()
import streamlit as st
import sqlite3
from app.utils import hide_streamlit_ui
hide_streamlit_ui()

if "user" not in st.session_state or st.session_state["user"].get("email") != "admin@ratezap.com":
    st.warning("🚫 Admin access only.")
    st.stop()

st.title("🛡️ Subscription Management")

conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

users = c.execute("SELECT id, full_name, email, subscription_status, trial_start FROM users").fetchall()

for user in users:
    user_id, full_name, email, status, trial_start = user
    st.write(f"**👤 {full_name}** | 📧 {email} | 🔖 Status: {status} | 🗓️ Trial Start: {trial_start}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Upgrade to Pro", key=f"pro_{user_id}"):
            c.execute("UPDATE users SET subscription_status = ? WHERE id = ?", ("pro", user_id))
            conn.commit()
            st.success(f"✅ {full_name} upgraded to Pro!")

    with col2:
        if st.button(f"Expire Trial", key=f"expire_{user_id}"):
            c.execute("UPDATE users SET subscription_status = ? WHERE id = ?", ("expired", user_id))
            conn.commit()
            st.success(f"⚠️ {full_name}'s trial marked as expired.")

    st.markdown("---")
