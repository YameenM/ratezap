import streamlit as st
from datetime import datetime, timedelta
from app.utils import hide_streamlit_ui


st.set_page_config(page_title="Upgrade | RateZap", layout="centered", initial_sidebar_state="collapsed")
hide_streamlit_ui()

user = st.session_state.get("user", {})
if not user:
    st.warning("⚠️ Please log in.")
    st.stop()
    
    
# Trial countdown logic
trial_start = user.get("trial_start", "")
days_ago = ""
if trial_start:
    try:
        trial_date = datetime.strptime(trial_start, "%Y-%m-%d")
        expired_days = (datetime.now() - (trial_date + timedelta(days=7))).days
        if expired_days > 0:
            days_ago = f"🗓️ Trial expired {expired_days} day{'s' if expired_days > 1 else ''} ago."
    except:
        days_ago = ""

st.markdown(f"""
<div style='padding: 40px; background: linear-gradient(135deg, #1f2937, #facc15); border-radius: 16px; color: #111; text-align: center;'>
    <h1 style='font-size: 36px; color: #1e3a8a;'>⚠️ Your Trial Has Ended</h1>
    <p style='font-size: 18px;'>Hi <strong>{user.get("full_name", "")}</strong>, your free 7-day trial is over.</p>
    <p style='font-size: 16px;'>To keep using RateZap’s features, upgrade to Pro below.</p>
</div>
""", unsafe_allow_html=True)

# Pro Plan Section - Light/Dark Compatible
st.markdown("""
<div style='background-color:#f9fafb; color:#111; border-radius:12px; padding: 25px 20px; margin-top:30px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); text-align:center;'>
    <h2 style='margin-bottom:12px;'>🌟 Pro Plan</h2>
    <p style='font-size:22px; color:#10b981; margin-bottom:10px;'><strong>$9/month</strong> <span style="font-size:14px; color:#666;"></span></p>
    <ul style='list-style:none; font-size: 16px; line-height: 1.8; padding: 0;'>
        <li>📊 Dynamic rate suggestions</li>
        <li>📅 Night audit + annual planner</li>
        <li>📬 Email alerts + forecast</li>
        <li>🔍 Rate Optimizer & Revenue Projection</li>
        <li>✈️ Annual Rate Generator for Tour Opretor/Company</li>
        <li>✅ Email & PDF exports</li>
        <li>🤝 Priority support</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Upgrade Request Section
st.markdown("### 📩 Request Pro Access")
if st.button("🎫 Request Manual Upgrade"):
    st.success("✅ Request received. Our team will contact you shortly.")

# Back to login
if st.button("🔙 Back to Login"):
    st.switch_page("Home.py")

st.markdown("---")
st.markdown("Need help? Email us at [support@ratezap.com](mailto:support@ratezap.com)")
