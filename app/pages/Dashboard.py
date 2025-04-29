import streamlit as st
st.set_page_config(page_title="Dashboard | RateZap", layout="wide", initial_sidebar_state="collapsed")
import sqlite3
import os
from datetime import datetime
from helpers.ota_links import display_ota_links_inline
import pandas as pd
from helpers.weather import get_user_city, get_weather_for_city
from utils import hide_streamlit_ui

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

# 🚀 Animated Page Header (Fade-In)
st.markdown("""
    <div style="
        text-align: center;
        animation: fadeIn 2s;
        font-size: 40px;
        color: #39FF14;;
        margin-bottom: 40px;
    ">
        📝 Dashboard
    </div>

    <style>
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home.py")
    st.stop()

# ➡️ Custom Top Navigation Bar
# Split layout into 7 equal columns
# ➡️ Custom Top Navigation Bar (Fixed UX/UI Version)

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
            st.switch_page("pages/Dashboard.py")

    with nav_col2:
        if st.button("📄 Annual Rates"):
            st.switch_page("pages/AnnualRates.py")

    with nav_col3:
        if st.button("🛏️ Night Audit"):
            st.switch_page("pages/NightAudit.py")

    with nav_col4:
        if st.button("🕓 Audit History"):
            st.switch_page("pages/VisualAuditHistory.py")

    with nav_col5:
        if st.button("📈 Rate Optimizer"):
            st.switch_page("pages/RateOptimizer.py")

    with nav_col6:
        if st.button("🏢 Companies List"):
            st.switch_page("pages/Companies.py")

    with nav_col7:
        if st.button("👤 My Profile"):
            st.switch_page("pages/Profile.py")
            
            
WEATHER_API_KEY = "76d5172810d44c39bf140434252504"

city = get_user_city()
condition, temp_c, icon_url = get_weather_for_city(city, WEATHER_API_KEY)
weather_display = f"<img src='{icon_url}' style='height:20px;vertical-align:middle;'> <strong>{condition}</strong>, {temp_c}°C"

# Check login
if "user" not in st.session_state:
    st.warning("⚠️ You have been logged out. Redirecting...")
    st.markdown("[Go to login](./)")
    st.markdown('<meta http-equiv="refresh" content="2; url=./">', unsafe_allow_html=True)
    st.stop()

# DB Setup
db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

with sqlite3.connect(db_path, check_same_thread=False) as conn:
    c = conn.cursor()

# 📊 7-Day Insight Metrics
user = st.session_state["user"]
user_id = user.get("id")

seven_days_ago = datetime.now() - pd.Timedelta(days=7)
c.execute('''
    SELECT suggested_rate, occupancy, timestamp 
    FROM rate_history 
    WHERE user_id = ? AND timestamp >= ?
''', (user_id, seven_days_ago.strftime('%Y-%m-%d')))
rows = c.fetchall()

if rows:
    df = pd.DataFrame(rows, columns=["suggested_rate", "occupancy", "timestamp"])
    df = df.apply(pd.to_numeric, errors='coerce')
    avg_rate = round(df["suggested_rate"].mean(), 2)
    avg_occupancy = round(df["occupancy"].mean(), 2)
    entry_count = df.shape[0]
else:
    avg_rate = avg_occupancy = entry_count = 0
    
    #=========================================================

# Create user_settings table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    prop_type TEXT,
    prop_name TEXT,
    city TEXT,
    country TEXT,
    currency TEXT
)
''')
conn.commit()

###c.execute("DROP TABLE IF EXISTS rate_history")###
# Create rate_history table if it doesn't exist for Suggested Rate History
c.execute('''
CREATE TABLE IF NOT EXISTS rate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TEXT,
    occupancy INTEGER,
    competitor_rate REAL,
    local_event TEXT,
    day_type TEXT,
    currency TEXT,
    suggested_rate REAL,
    hotel_name TEXT
)
''')
conn.commit()


# Get user ID and info
user = st.session_state["user"]
user_id = user.get("id")
full_name = user.get("full_name", "Guest")

# Load customization from session
custom_data = st.session_state["custom_data"]
prop_name = custom_data.get("prop_name", "")
custom_city = custom_data.get("city", "")
custom_country = custom_data.get("country", "")
currency = custom_data.get("currency", "$")

# 🔗 Action Buttons (top right)
#col_top_spacer, col_button1, col_button2 = st.columns([9, 1.5, 1.5])
#with col_button1:
    #if st.button("🅰️ Night Audit"):
        #st.switch_page("pages/NightAudit.py")
#with col_button2:
    #if st.button("📄 Annual Rates"):
        #st.switch_page("pages/AnnualRates.py")


# --- ⚙️ Customize Dashboard ---
with st.expander("⚙️ Customize Dashboard", expanded=False):
    if "edit_mode" not in st.session_state:
        st.session_state["edit_mode"] = False
    edit = st.toggle("Edit Mode", value=st.session_state["edit_mode"])
    st.session_state["edit_mode"] = edit

    if edit:
        with st.form("custom_form"):
            prop_type = st.selectbox("Property Type", ["Hotel", "Hotel Apartments", "Motel", "Guest House", "Air BnB", "Boutique Hotel"])
            prop_name_input = st.text_input("Property Name", value=prop_name)
            city_input = st.text_input("City", value=custom_city)
            country_input = st.text_input("Country", value=custom_country)
            currency_input = st.selectbox("Preferred Currency", ["$", "AED", "PKR", "₹", "€", "£", "CAD", "AUD"], index=0)
            confirm = st.checkbox("✅ Confirm to Save")
            submitted = st.form_submit_button("💾 Save Changes")
            if submitted:
                if confirm:
                    # Update DB
                    c.execute("REPLACE INTO user_settings (user_id, prop_type, prop_name, city, country, currency) VALUES (?, ?, ?, ?, ?, ?)", (
                        user_id, prop_type, prop_name_input, city_input, country_input, currency_input
                    ))
                    conn.commit()
                    # Update session
                    st.session_state["custom_data"] = {
                        "prop_type": prop_type,
                        "prop_name": prop_name_input,
                        "city": city_input,
                        "country": country_input,
                        "currency": currency_input
                    }
                    st.success("✅ Dashboard updated.")
                    st.rerun()
                else:
                    st.warning("Please confirm before saving.")
    else:
        saved = st.session_state["custom_data"]
        st.markdown(f"""
        - **Property Type**: {saved.get("prop_type", "N/A")}
        - **Property Name**: {saved.get("prop_name", "N/A")}
        - **City**: {saved.get("city", "N/A")}
        - **Country**: {saved.get("country", "N/A")}
        - **Currency**: {saved.get("currency", "$")}
        """)

# Header
current_date = datetime.now().strftime("%A, %b %d, %Y")
current_time = datetime.now().strftime("%I:%M %p")
print("🌍 Using city for weather:", custom_city)


st.markdown(f"""
<div style='
    background-color: var(--secondary-background-color);
    color: var(--text-color);
    padding: 20px 30px;
    border-radius: 12px;
    margin-bottom: 20px;
    border: 1px solid rgba(125,125,125,0.2);'>
  <div style='display:flex; justify-content:space-between; align-items:center;'>
    <div style='display:flex; align-items:center; gap:16px; flex: 1;'>
      <div style='font-size: 58px;'>👤</div>
      <div>
        <h3 style='margin: 0;'>Welcome, {full_name}</h3>
        <p style='font-size:16px;color:#777;'> 🗓️ {current_date} | ⏰ {current_time} |  {weather_display} </p>
      </div>
    </div>
    <div style='text-align:right; font-size:20px;'>
      {"<p style='margin: 4px 20px;'>🏨 " + prop_name + "</p>" if prop_name else ""}
      {"<p style='margin: 4px 20px;'>📍 " + custom_city + ", " + custom_country + "</p>" if custom_city else ""}
  </div>
  <!-- 📊 Metrics Area -->
    <div style='
        background-color: #fff3cd;
        color: #333;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #ffca2c;
        width: 280px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;'>
        <h4 style='margin-bottom:10px;'>📊 7-Day Insights</h4>
        <p style='margin: 0 0 6px 0;'><strong>Avg. Rate:</strong> {currency} {avg_rate}</p>
        <p style='margin: 0 0 6px 0;'><strong>Avg. Occupancy:</strong> {avg_occupancy}%</p>
        <p style='margin: 0;'><strong>Entries:</strong> {entry_count}</p>
    </div>
  
</div>


""", unsafe_allow_html=True)
####################Optimizer+=========================================
currency = st.session_state.get("custom_data", {}).get("currency", "PKR")

with st.expander("🧠 Smart Rate Optimizer (Insights)", expanded=False):
    conn = sqlite3.connect("ratezap.db", check_same_thread=False)
    c = conn.cursor()
    user_id = st.session_state["user"]["id"]

    c.execute('''
        SELECT suggested_rate, occupancy, timestamp FROM rate_history
        WHERE user_id = ?
        ORDER BY datetime(timestamp) DESC LIMIT 30
    ''', (user_id,))
    rows = c.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["Rate", "Occupancy", "Timestamp"])
        df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
        df["Occupancy"] = pd.to_numeric(df["Occupancy"], errors="coerce")

        avg_rate = round(df["Rate"].mean(), 2)
        avg_occ = round(df["Occupancy"].mean(), 1)

        if avg_occ > 75:
            tip = "❇️ High occupancy — consider increasing your rate slightly."
            bg = "rgba(209, 231, 221, 0.85)"
        elif avg_occ < 50:
            tip = "🔻 Low occupancy — try reducing base rates for a few days."
            bg = "rgba(255, 243, 205, 0.85)"
        else:
            tip = "🏦 Occupancy is stable — monitor competition before adjusting."
            bg = "rgba(222, 226, 230, 0.85)"

        st.markdown(f"""
        <div style='
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 18px 24px;
        border-radius: 10px;
        border-left: 6px solid #6c757d;
        font-size: 16px;
        line-height: 1.7;
        '>
        <strong>📊 Summary:</strong><br>
        🪙 Avg. Rate (30d): <strong>{currency} {avg_rate}</strong> &nbsp;&nbsp;|&nbsp;&nbsp;
        🏨 Avg. Occupancy: <strong>{avg_occ}%</strong><br><br>
        💡 <strong>Tip:</strong> {tip}
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button("➡️ Full Optimizer", key="open_optimizer_btn"):
                st.switch_page("pages/RateOptimizer.py")
    else:
        st.info("No recent rate data available. Save some rate suggestions first.")

#===========================================
# Room Inputs
st.markdown("### 🏨 Room & Rate Details")
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_rooms = st.number_input("Total Rooms", min_value=0, value=0)
with col2:
    out_of_order = st.number_input("Out of Order", min_value=0, value=0)
with col3:
    dirty_rooms = st.number_input("Dirty/Checkout Rooms", min_value=0, value=0)

max_occupied = max(total_rooms - out_of_order - dirty_rooms, 0)
with col4:
    occupied_rooms = st.number_input("Occupied Rooms", min_value=0, max_value=max_occupied, value=0)


available_rooms = total_rooms - out_of_order - dirty_rooms - occupied_rooms
# 🧮 Calculate dynamic occupancy percentage
if total_rooms > 0:
    calculated_occupancy = int((occupied_rooms / total_rooms) * 100)
    progress_value = min(occupied_rooms / total_rooms, 1.0)  # cap to 100%
else:
    calculated_occupancy = 0
    progress_value = 0
    st.progress(progress_value)

st.success(f"✅ Total Available Rooms for Sale: {available_rooms} +  🟥 Checkout Rooms 🛌")

# Rate Inputs
st.markdown("### 💵 Pricing Input")
col5, col6, col7 = st.columns(3)
with col5:
    rack_rate = st.number_input(f"Property Rack Rate ({currency})", min_value=0.0, value=0.0)
with col6:
    comp_rate = st.number_input(f"Competitor Rate ({currency})", min_value=0.0, value=0.0)
with col7:
    col_occ1, col_occ2 = st.columns([2, 1])
    with col_occ1:
        st.markdown("**Calculated Occupancy** 🏦")
        st.progress(calculated_occupancy / 100)
    with col_occ2:
        st.markdown(f"<div style='font-size:18px; color:#2b6cb0; text-align:left; padding-top: 6px;'><strong>{calculated_occupancy}%</strong></div>", unsafe_allow_html=True)


col8, col9, col10 = st.columns(3)
with col8:
    day_type = st.radio("Day?", ["Weekday", "Weekend"], index=0)
with col9:
    event_today = st.radio("Event Today?", ["Yes", "No"], index=1)
with col10:
    holidays = st.radio("Holiday Today?", ["Yes", "No"], index=1)

target_rate = st.number_input(f"🎯 Targeted Nightly Rate ({currency})", min_value=0.0, value=0.0)

# Suggestion Summary
currency_symbol_map = {
    "$": "🇺🇸$", "AED": "🇦🇪AED", "PKR": "🇵🇰Rs", "₹": "🇮🇳₹", "€": "💶€", "£": "🇬🇧£", "CAD": "🇨🇦C$", "AUD": "🇦🇺A$"
}
symbol = currency_symbol_map.get(currency, currency)

if st.button("💡 Get Suggested Rate"):
    rate = comp_rate
    reasons = []
    confidence = 0
    confidence_reasons = []

    saleable_rooms = available_rooms + dirty_rooms
    occupancy_ratio = occupied_rooms / total_rooms if total_rooms else 0


    # Confidence Scoring
    if total_rooms > 0:
        confidence += 20
        confidence_reasons.append("Occupancy data available")
    if comp_rate > 0:
        confidence += 20
        confidence_reasons.append("Competitor rate provided")
    if saleable_rooms > 0:
        confidence += 10
        confidence_reasons.append("Saleable room data present")
    confidence += 10  # Always count day type
    if event_today == "Yes" or holidays == "Yes":
        confidence += 20
        confidence_reasons.append("Event or holiday noted")

    # --- Rate Adjustments ---
    if occupancy_ratio < 0.4:
        adjustment = rate * 0.10
        rate -= adjustment
        reasons.append(f"Low occupancy (−10% = {symbol} {adjustment:.2f})")
    elif occupancy_ratio > 0.8:
        adjustment = rate * 0.10
        rate += adjustment
        reasons.append(f"High occupancy (+10% = {symbol} {adjustment:.2f})")

    if day_type == "Weekend":
        adjustment = rate * 0.12
        rate += adjustment
        reasons.append(f"Weekend (+12% = {symbol} {adjustment:.2f})")

    if event_today == "Yes":
        adjustment = rate * 0.15
        rate += adjustment
        reasons.append(f"Local event today (+15% = {symbol} {adjustment:.2f})")

    if holidays == "Yes":
        adjustment = rate * 0.10
        rate += adjustment
        reasons.append(f"Holiday (+10% = {symbol} {adjustment:.2f})")

    if saleable_rooms < 10:
        adjustment = rate * 0.08
        rate += adjustment
        reasons.append(f"Low available rooms (+8% = {symbol} {adjustment:.2f})")
    elif saleable_rooms > 50:
        adjustment = rate * 0.05
        rate -= adjustment
        reasons.append(f"High availability (−5% = {symbol} {adjustment:.2f})")

    rate = round(rate, 2)

    # --- Confidence Message ---
    if confidence >= 80:
        level = "🔵 High"
    elif confidence >= 50:
        level = "🟡 Medium"
    else:
        level = "🔴 Low"

    st.success(f"💡 RateZap Suggested Rate: {symbol} {rate:.2f} for 👉 Family Room (2 adults 👤👤 + 1 child 🧒)")
    st.markdown(f"""
    <div style='
        background-color: rgba(44, 62, 80, 0.9); 
        color: white;
        padding: 16px 20px;
        border-radius: 10px; 
        border-left: 5px solid #2b6cb0;
        margin-top: 12px;
        font-size: 15px;
    '>
    <strong style="font-size: 17px;">{level} Confidence ({confidence}%)</strong><br><br>
    {"<br>".join(f"✅ {r}" for r in confidence_reasons)}
    </div>
    """, unsafe_allow_html=True)

    single_rate = round(rate * 0.80, 2)
    double_rate = round(rate * 0.90, 2)

    st.markdown(f"""
    <div style='background-color: #fff3cd; color: #000; margin-bottom: 20px; padding: 12px 18px; margin-top: 12px; border-left: 4px solid #2b6cb0; border-radius: 6px; font-size: 15px;'>
    🔵 {symbol} {single_rate:.2f} for 1 Room (1 Person 👤)<br>
    🔵 {symbol} {double_rate:.2f} for 1 Room (2 Persons 👤👤)<br>
    🔵 {symbol} {rate:.2f} for Family Room (2 adults 👤👤 + 1 child 🧒)
    </div>
    """, unsafe_allow_html=True)
    
    st.info("📌 Reason: \n- " +  " \n-  ".join(reasons))
    
    # === 📅 Styled 3-Day Rate Forecast ===
st.markdown("### 🪄 3-Day Rate Forecast")

# Get past 14 days of rate history for current user
today = datetime.now()
past_14 = (today - pd.Timedelta(days=14)).strftime('%Y-%m-%d')
past_7 = (today - pd.Timedelta(days=7)).strftime('%Y-%m-%d')

# Fetch rates
c.execute('''
    SELECT timestamp, suggested_rate FROM rate_history
    WHERE user_id = ? AND timestamp >= ?
    ORDER BY timestamp DESC
''', (user_id, past_14))
all_rows = c.fetchall()

if all_rows:
    rate_df = pd.DataFrame(all_rows, columns=["timestamp", "rate"])
    rate_df["timestamp"] = pd.to_datetime(rate_df["timestamp"])
    rate_df["rate"] = pd.to_numeric(rate_df["rate"], errors='coerce')

    # 7-day and 14-day averages
    last_14_avg = round(rate_df["rate"].mean(), 2)
    last_7_avg = round(rate_df[rate_df["timestamp"] >= past_7]["rate"].mean(), 2)

    trend_up = last_7_avg > last_14_avg
    rate_shift = 0.03 if trend_up else -0.03
    trend_icon = "📈" if trend_up else "📉"
    trend_label = "Rising" if trend_up else "Falling"

    total_entries = len(rate_df)
    if total_entries >= 10:
        emoji = "🔵 High"
    elif total_entries >= 5:
        emoji = "🟡 Medium"
    else:
        emoji = "🔴 Low"

    base_rate = last_7_avg if last_7_avg > 0 else last_14_avg
    forecast = []
    for i in range(1, 4):
        date = today + pd.Timedelta(days=i)
        forecast_rate = round(base_rate * (1 + rate_shift + (0.01 * i)), 2)
        forecast.append((date.strftime('%a, %b %d'), forecast_rate))

    # Styled output
    st.markdown(f"""
<div style='
    background-color: rgba(40, 44, 52, 0.95); 
    color: #f0f0f0;
    padding: 20px;
    border-radius: 12px; 
    border-left: 6px solid #2b6cb0;
    font-size: 16px;
    line-height: 1.8;
    margin-bottom: 20px;
'>
    <div><strong>📊 Forecast Summary:</strong><br>
    🗓️ <strong>7️-Day Avg:</strong> {currency} {last_7_avg} &nbsp;&nbsp;|&nbsp;&nbsp;
    🗓️ <strong>14-Day Avg:</strong> {currency} {last_14_avg} &nbsp;&nbsp;|&nbsp;&nbsp;
    {trend_icon} <strong>Trend:</strong> {trend_label} &nbsp;&nbsp;|&nbsp;&nbsp;
    🌞 <strong>Confidence:</strong> {emoji}
    </div>
    <br>
    <div><strong>✨ Forecast:</strong></div>
    <ul style='padding-left: 20px; margin-top: 8px;'>
        <li>📅👉 <strong>{forecast[0][0]}</strong> → {currency} {forecast[0][1]}</li>
        <li>📅👉 <strong>{forecast[1][0]}</strong> → {currency} {forecast[1][1]}</li>
        <li>📅👉 <strong>{forecast[2][0]}</strong> → {currency} {forecast[2][1]}</li>
    </ul>
</div>
""", unsafe_allow_html=True)


else:
    st.info("Not enough rate history to forecast. Save a few suggestions first.")

    # 📥 Save to history
if "rate" not in locals():
    st.warning("ℹ️ Please scroll ☝️ up, fill in all required fields, and click '💡 Get Suggested Rate' to generate your rate suggestion.")
    st.stop()

occupancy_ratio = occupied_rooms / total_rooms if total_rooms > 0 else 0

display_ota_links_inline(prop_name or "My Hotel", custom_city or user.get("city", "City"))

c.execute('''
    INSERT INTO rate_history (
        user_id,
        timestamp,
        occupancy,
        competitor_rate,
        local_event,
        day_type,
        currency,
        suggested_rate,
        hotel_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    user_id,
    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    int(occupancy_ratio * 100),
    comp_rate,
    event_today,
    day_type,
    currency,
    rate,
    prop_name))
conn.commit()


# What If Testing Mode======================================================================  
with st.expander("🧪 What-If Testing Mode (Simulate Rates)", expanded=False):
    st.markdown("Try different combinations to see how they affect the suggested rate and confidence score. This won’t save anything.")

    col1, col2, col3 = st.columns(3)
    with col1:
        test_total_rooms = st.number_input("Total Rooms", min_value=0, value=50, key="test_total")
        test_out_of_order = st.number_input("Out of Order", min_value=0, value=2, key="test_ooo")
    with col2:
        test_dirty_rooms = st.number_input("Dirty/Checkout", min_value=0, value=3, key="test_dirty")
        test_occupied = st.number_input("Occupied Rooms", min_value=0, value=30, key="test_occupied")
    with col3:
        test_comp_rate = st.number_input(f"Competitor Rate ({currency})", min_value=0.0, value=9000.0, key="test_comp")
        test_day = st.radio("Day Type", ["Weekday", "Weekend"], horizontal=True, key="test_day")
        test_event = st.radio("Event Today?", ["Yes", "No"], horizontal=True, key="test_event")
        test_holiday = st.radio("Holiday?", ["Yes", "No"], horizontal=True, key="test_holiday")

    if st.button("🧪 Run Simulation"):
        available_rooms = test_total_rooms - test_out_of_order - test_dirty_rooms - test_occupied
        saleable_rooms = available_rooms + test_dirty_rooms
        occupancy_ratio = (test_occupied / test_total_rooms) if test_total_rooms > 0 else 0

        test_rate = test_comp_rate
        reasons = []
        confidence = 0
        confidence_reasons = []

        if test_total_rooms > 0:
            confidence += 20
            confidence_reasons.append("✅ Occupancy data available")
        if test_comp_rate > 0:
            confidence += 20
            confidence_reasons.append("✅ Competitor rate provided")
        if saleable_rooms > 0:
            confidence += 10
            confidence_reasons.append("✅ Saleable room data present")
        confidence += 10
        if test_event == "Yes" or test_holiday == "Yes":
            confidence += 20
            confidence_reasons.append("✅ Event or holiday noted")

        if occupancy_ratio < 0.4:
            adj = test_rate * 0.10
            test_rate -= adj
            reasons.append(f"Low occupancy (−10% = {currency} {adj:.2f})")
        elif occupancy_ratio > 0.8:
            adj = test_rate * 0.10
            test_rate += adj
            reasons.append(f"High occupancy (+10% = {currency} {adj:.2f})")
        if test_day == "Weekend":
            adj = test_rate * 0.12
            test_rate += adj
            reasons.append(f"Weekend (+12% = {currency} {adj:.2f})")
        if test_event == "Yes":
            adj = test_rate * 0.15
            test_rate += adj
            reasons.append(f"Local event (+15% = {currency} {adj:.2f})")
        if test_holiday == "Yes":
            adj = test_rate * 0.10
            test_rate += adj
            reasons.append(f"Holiday (+10% = {currency} {adj:.2f})")
        if saleable_rooms < 10:
            adj = test_rate * 0.08
            test_rate += adj
            reasons.append(f"Low availability (+8% = {currency} {adj:.2f})")
        elif saleable_rooms > 50:
            adj = test_rate * 0.05
            test_rate -= adj
            reasons.append(f"High availability (−5% = {currency} {adj:.2f})")

        test_rate = round(test_rate, 2)
        level = "🔵 High" if confidence >= 80 else "🟡 Medium" if confidence >= 50 else "🔴 Low"

        st.success(f"💡 Simulated Suggested Rate: {currency} {test_rate:.2f} for 👉 Family Room (2 adults 👤👤 + 1 child 🧒)")
        st.markdown(f"""
        <div style='background-color: rgba(44, 62, 80, 0.95); color: white; padding: 16px 20px; border-radius: 10px; border-left: 5px solid #2b6cb0; font-size: 15px; line-height: 1.6; margin-top: 10px;'>
            <strong>{level} Confidence ({confidence}%)</strong><br>
            {"<br>".join(confidence_reasons)}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: #fff3cd; color: #000; margin-bottom: 20px; padding: 12px 18px; margin-top: 12px; border-left: 4px solid #2b6cb0; border-radius: 6px; font-size: 15px;'>
        🔵 {currency} {round(test_rate * 0.80, 2)} for 1 Room (1 Person 👤)<br>
        🔵 {currency} {round(test_rate * 0.90, 2)} for 1 Room (2 Persons 👤👤)<br>
        🔵 {currency} {test_rate:.2f} for Family Room (2 adults 👤👤 + 1 child 🧒)
        </div>
        """, unsafe_allow_html=True)

        st.info("📌 Reason: \n- " +  " \n-  ".join(reasons))
        
        if st.button("📥 Copy to Main Input"):
            st.session_state["total_rooms"] = test_total_rooms
            st.session_state["out_of_order"] = test_out_of_order
            st.session_state["dirty_rooms"] = test_dirty_rooms
            st.session_state["occupied_rooms"] = test_occupied
            st.session_state["comp_rate"] = test_comp_rate
            st.session_state["day_type"] = test_day
            st.session_state["event_today"] = test_event
            st.session_state["holiday_today"] = test_holiday
            st.success("✅ Values copied to main input. Scroll up to apply and save.")


   
# 🧠 Get last 10 rate suggestions
# ===============================
# 📊 Rate History Viewer
# ===============================
with st.expander("📈 View Last 10 Rate Suggestions", expanded=True):
    c.execute('''
        SELECT timestamp, suggested_rate, occupancy, day_type, local_event, competitor_rate, currency
        FROM rate_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (user_id,))
    rate_rows = c.fetchall()

    if rate_rows:
        rate_df = pd.DataFrame(rate_rows, columns=[
            "Timestamp", "Suggested Rate", "Occupancy %", "Day Type", "Event", "Competitor Rate", "Currency"
        ])
        
        # Show Data Table
        st.markdown("#### 📋 History Table")
        st.dataframe(rate_df, use_container_width=True)

        # Show Trend Chart
        st.markdown("#### 📊 Rate Trend (Last 10)")
        chart_data = rate_df[["Timestamp", "Suggested Rate"]].copy()
        chart_data["Timestamp"] = pd.to_datetime(chart_data["Timestamp"])
        st.line_chart(chart_data.set_index("Timestamp"))

    else:
        st.info("No rate suggestions saved yet. Try using '💡 Get Suggested Rate' to generate one.")
        
