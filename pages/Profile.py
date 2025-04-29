
import streamlit as st
import sqlite3

import streamlit as st
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

# 🔥 Page Header (Center aligned, nice style)
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 40px;font-size: 36px; color: #39FF14;'>
         👤 My Profile
    </h1>
""", unsafe_allow_html=True)


# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home.py")
    st.stop()

import streamlit as st
from utils import hide_streamlit_ui

# Hide Sidebar
hide_streamlit_ui()


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
            
st.markdown("---")  # Nice separator line



# Check login
if "user" not in st.session_state:
    st.warning("⚠️ Please login first.")
    st.stop()

st.title(" 👤 My Profile ✍️")

# DB Connection
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()

user_id = st.session_state["user"]["id"]

# Load current data
c.execute("SELECT hotel_name, city, country, phone FROM users WHERE id = ?", (user_id,))
row = c.fetchone()

hotel_name = st.text_input("🏨 Hotel Name", value=row[0] if row else "")
city = st.text_input("🌆 City", value=row[1] if row else "")
country = st.text_input("🌍 Country", value=row[2] if row else "")
phone = st.text_input("📞 Phone", value=row[3] if row else "")

if st.button("💾 Save Changes"):
    c.execute("""
        UPDATE users 
        SET hotel_name = ?, city = ?, country = ?, phone = ?
        WHERE id = ?
    """, (hotel_name, city, country, phone, user_id))
    conn.commit()
    st.success("✅ Profile updated successfully!")
