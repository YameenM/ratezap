# pages/RateOptimizer.py

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import altair as alt

st.set_page_config(page_title="Rate Optimizer & Projections", layout="wide")

import streamlit as st
from app.utils import hide_streamlit_ui


# Hide Streamlit sidebar completely
hide_streamlit_ui()

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
         📈 Rate Optimizer
    </h1>
""", unsafe_allow_html=True)


# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home")
    st.stop()

import streamlit as st
from app.utils import hide_streamlit_ui

# Hide Sidebar
hide_streamlit_ui()

# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home")
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
            st.switch_page("Dashboard")

    with nav_col2:
        if st.button("📄 Annual Rates"):
            st.switch_page("AnnualRates")

    with nav_col3:
        if st.button("🛏️ Night Audit"):
            st.switch_page("NightAudit")

    with nav_col4:
        if st.button("🕓 Audit History"):
            st.switch_page("VisualAuditHistory")

    with nav_col5:
        if st.button("📈 Rate Optimizer"):
            st.switch_page("RateOptimizer")

    with nav_col6:
        if st.button("🏢 Companies List"):
            st.switch_page("Companies")

    with nav_col7:
        if st.button("👤 My Profile"):
            st.switch_page("Profile")

st.markdown("---")  # Nice separator line


# 🔐 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home")
    st.stop()
    

# DB
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()
user_id = st.session_state["user"]["id"]
hotel_name = st.session_state.get("custom_data", {}).get("prop_name", "Hotel")
currency = st.session_state.get("custom_data", {}).get("currency", "PKR")
symbol_map = {"PKR": "Rs.", "₹": "₹", "USD": "$", "$": "$", "AED": "AED", "€": "€", "£": "£"}
symbol = symbol_map.get(currency, currency)

st.markdown("## 📊 Rate Optimizer & Revenue Projection")
st.info("Analyze past 30-day performance and forecast annual revenue based on adjustable inputs.")

# Fetch data
past_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
c.execute('''
    SELECT timestamp, suggested_rate, occupancy FROM rate_history
    WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp
''', (user_id, past_30))
rows = c.fetchall()

if rows:
    df = pd.DataFrame(rows, columns=["timestamp", "rate", "occupancy"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df["occupancy"] = pd.to_numeric(df["occupancy"], errors="coerce")

    avg_rate = round(df["rate"].mean(), 2)
    avg_occ = round(df["occupancy"].mean(), 2)
    trend_rate_icon = "🔺" if df["rate"].iloc[-1] > df["rate"].iloc[0] else "🔻"
    trend_occ_icon = "🔺" if df["occupancy"].iloc[-1] > df["occupancy"].iloc[0] else "🔻"

    # 📈 Inline Summary
    st.markdown(f"""
    <div style='
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 16px;
        border-left: 6px solid #2b6cb0;
        border-radius: 10px;
        font-size: 16px;
        margin-bottom: 20px;
    '>
        <strong>📈 Summary:</strong><br>
        {trend_rate_icon} <strong>Avg. Rate (30d):</strong> {symbol}{avg_rate} &nbsp;&nbsp;|&nbsp;&nbsp;
        {trend_occ_icon} <strong>Avg. Occupancy:</strong> {avg_occ:.1f}%
    </div>
    """, unsafe_allow_html=True)
    
    # Recommendation
    if avg_occ < 40:
        st.warning("⚠️ Low occupancy trend. Consider **reducing** base rates to stay competitive.")
    elif avg_occ > 80:
        st.success("⚡️ High occupancy trend. You may consider **increasing** rates to maximize revenue.")
    else:
        st.info("📊 Occupancy stable. Maintain current pricing strategy.")

    # Projection Controls
    st.markdown("#### 🧮 Projected Revenue Calculator")
    col1, col2 = st.columns(2)
    with col1:
        num_rooms = st.slider("🛏️ Total Rooms", 10, 300, 60)
    with col2:
        occ_input = st.slider("📊 Occupancy %", 30, 100, int(avg_occ))

    revenue = round(avg_rate * (occ_input / 100) * num_rooms * 365)

    st.markdown(f"**🏨 Property:** {hotel_name}")
    st.markdown(f"**📆 Projected Year Revenue:** `{symbol}{revenue:,.0f}`")
    st.markdown(f"**📈 Based on:** Avg. ADR `{symbol}{avg_rate:,.2f}` | Occupancy `{occ_input}%` | Rooms `{num_rooms}`")

    # 🔻 Chart
    st.markdown("### 📉 30-Day Trend")
    chart_df = df.rename(columns={"rate": "Avg Rate", "occupancy": "Occupancy (%)"})
    chart = alt.Chart(chart_df).transform_fold(
        ["Avg Rate", "Occupancy (%)"],
        as_=["Metric", "Value"]
    ).mark_line(point=True).encode(
        x=alt.X("timestamp:T", title="Date"),
        y=alt.Y("Value:Q"),
        color=alt.Color("Metric:N")
    ).properties(height=320)

    st.altair_chart(chart, use_container_width=True)

else:
    st.warning("Not enough data to display optimizer trends.")