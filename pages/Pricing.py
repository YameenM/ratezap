
import streamlit as st
st.set_page_config(page_title="Pricing | RateZap", layout="wide")
from utils import hide_streamlit_ui
hide_streamlit_ui()


# 🔍 Get user country from session (fallback to 'World')
user_country = st.session_state.get("custom_data", {}).get("country", "World")

if user_country.lower() in ["pakistan", "pk"]:
    currency = "PKR"
    monthly = "₨1,999"
    yearly = "₨19,999"
elif user_country.lower() in ["uae", "united arab emirates", "ae"]:
    currency = "AED"
    monthly = "AED 79"
    yearly = "AED 790"
else:
    currency = "USD"
    monthly = "$15"
    yearly = "$150"

plans = [
    {"name": "🎁 Free Trial", "price": "Free", "duration": "7 Days", "features": ["✅ Full Dashboard", "✅ Email Alerts", "✅ Forecasting"]},
    {"name": "💼 Pro Monthly", "price": monthly, "duration": "Monthly", "features": ["📊 Unlimited Reports", "📧 Email Support", "📈 Forecasting"]},
    {"name": "🏆 Pro Yearly", "price": yearly, "duration": "Yearly", "features": ["🎁 Save 2 Months", "⏱ Priority Support", "📤 PDF/CSV Export"]},
]



# 💳 Render Cards
st.markdown("<h2 style='text-align:center;'>💰 RateZap Subscription Plans</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;'>🌍 Prices are shown in <strong>{currency}</strong> based on your country: <em>{user_country}</em></p>", unsafe_allow_html=True)

# 💅 Card Styling
st.markdown("""
    <style>
    .pricing-wrapper {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        gap: 24px;
        overflow-x: auto;
        padding: 60px 100px;
        scroll-snap-type: x mandatory;
    }

    .pricing-card {
        flex: 0 0 300px;
        scroll-snap-align: start;
        background-color: var(--background-color);
        color: var(--text-color);
        border-radius: 16px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        padding: 24px;
        transition: all 0.3s ease-in-out;
    }

    .pricing-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }

    .pricing-card h3 {
        margin-top: 0;
        font-size: 1.5rem;
    }

    .price {
        font-size: 2rem;
        font-weight: bold;
        margin: 8px 0;
    }

    .features {
        font-size: 0.95rem;
        margin-top: 16px;
        line-height: 1.6;
    }

    </style>

    <div class="pricing-wrapper">
        <div class="pricing-card">
            <h3>🎁 Free Trial</h3>
            <div class="price">Free</div>
            <div class="features">
                ✅ Full Dashboard<br>
                ✅ Email Alerts<br>
                ✅ Forecasting<br>
                <br>Duration: <strong>7 Days</strong>
            </div>
        </div>
        <div class="pricing-card">
            <h3>💼 Pro Monthly</h3>
            <div class="price">$15</div>
            <div class="features">
                ✅ All Features<br>
                ✅ OTA Links<br>
                ✅ Smart Optimizer<br>
                <br>Billed Monthly
            </div>
        </div>
        <div class="pricing-card">
            <h3>🏆 Pro Annual</h3>
            <div class="price">$150</div>
            <div class="features">
                ✅ Everything in Pro<br>
                ✅ PDF & Email Reports<br>
                ✅ Admin Support<br>
                <br>Save 17% yearly
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
