# 📄 File: pages/Pricing.py
import streamlit as st

st.set_page_config(page_title="Pricing | RateZap", layout="wide")
st.markdown("## 💼 Subscription Plans for RateZap")

plans = [
    {"name": "Free Trial", "price": "₹0", "duration": "7 Days", "features": ["All features", "No card required"]},
    {"name": "Pro Monthly", "price": "₹1,999", "duration": "Monthly", "features": ["Full Dashboard", "Email Alerts", "Forecast"]},
    {"name": "Pro Yearly", "price": "₹19,999", "duration": "Yearly", "features": ["2 months free", "Priority Support"]},
]

for plan in plans:
    with st.container():
        st.markdown(f"""
        <div style='border:1px solid #ccc; padding: 20px; border-radius:10px; margin:10px 0;'>
            <h3>{plan['name']}</h3>
            <p><strong>{plan['price']}</strong> — {plan['duration']}</p>
            <ul>{"".join(f"<li>{f}</li>" for f in plan['features'])}</ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("👉 Contact us to activate your plan or request a custom quote.")
