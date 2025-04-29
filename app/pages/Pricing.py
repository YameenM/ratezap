import streamlit as st
st.set_page_config(page_title="Pricing | RateZap", layout="wide", initial_sidebar_state="collapsed")
from app.utils import hide_streamlit_ui

hide_streamlit_ui()


if st.button("✍️ Register/Login"):
        st.switch_page("Home")
        
# 💼 Title Section
st.markdown("""
<div style='text-align:center; margin-top: 30px; margin-bottom: 50px;'>
    <h1 style='font-size: 36px;'>💼 RateZap Pricing</h1>
    <p style='font-size: 18px; color: #ccc;'>Choose the plan that fits your hotel’s needs:</p>
</div>
""", unsafe_allow_html=True)

# 🔄 Plans in Columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style='background-color:#f9fafb; color:#111; padding: 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
        <h2 style='color:#1f2937;'>🌟 Pro Plan</h2>
        <p style='font-size:24px; color:#10b981;'><strong>$19/month</strong></p>
        <ul style='font-size:16px; line-height: 1.8;'>
            <li>💰 Daily rate suggestions</li>
            <li>📊 Forecast emails & reports</li>
            <li>🔍  Night audit analyzer</li>
            <li>🏦 Annual rate planner</li>
            <li>📤 PDF / CSV export</li>
        </ul>
        <p style='font-size:14px;color:#555;'>Best for independent hotels</p>
        <button style='margin-top:15px; padding:10px 20px; border:none; border-radius:8px; background-color:#10b981; color:white; font-size:16px;'>Upgrade Now</button>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background-color:#f3f4f6; color:#111; padding: 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
        <h2 style='color:#1f2937;'>🏢 Plus Plan</h2>
        <p style='font-size:24px; color:#3b82f6;'><strong>$29/month</strong></p>
        <ul style='font-size:16px; line-height: 1.8;'>
            <li>✔️ Everything in Pro</li>
            <li>👥 Multi-user login support</li>
            <li>🗂️ Rate & audit history archive</li>
            <li>📞 Priority support</li>
            <li>🔓 Beta feature access</li>
        </ul>
        <p style='font-size:14px;color:#555;'>For teams or multi-property hotels</p>
        <button style='margin-top:15px; padding:10px 20px; border:none; border-radius:8px; background-color:#3b82f6; color:white; font-size:16px;'>Contact Sales</button>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center'>💡 Need something custom? <a href='mailto:support@ratezap.com'>Contact us</a> for enterprise pricing.</div>", unsafe_allow_html=True)