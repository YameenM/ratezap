from utils import hide_streamlit_ui

hide_streamlit_ui()
import streamlit as st
import os

# ⬛ Page config
st.set_page_config(page_title="📂 Sample Import Templates", layout="wide")

# Hide sidebar if needed (optional)
from app.utils import hide_streamlit_ui
hide_streamlit_ui()

# 🔒 Require login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.stop()

# 📦 Download location
TEMPLATE_ZIP_PATH = "RateZap_Sample_Import_Templates.zip"

if st.button("⬅️ Back to Night Audit"):
    st.switch_page("pages/NightAudit.py")

st.title("📂 Sample Import Templates")
st.markdown("""
Use these ready-made templates to prepare your Night Audit uploads quickly and correctly!  
You can choose a format that matches your hotel's system or needs.
""")

st.divider()

# 🛠 Template List
templates = [
    "Standard Format.xlsx",
    "Hilton Format.xlsx",
    "Marriott Format.xlsx",
    "Custom Minimal Format.xlsx",
    "Comprehensive Guest Format.xlsx",
    "Sample Night Audit.csv"
]

# 📥 Download Button
if os.path.exists(TEMPLATE_ZIP_PATH):
    with open(TEMPLATE_ZIP_PATH, "rb") as file:
        st.download_button(
            label="⬇️ Download All Templates (.zip)",
            data=file,
            file_name="RateZap_Sample_Import_Templates.zip",
            mime="application/zip"
        )
else:
    st.error("❌ Template ZIP not found. Please contact support.")

st.divider()

# 📃 Templates list display
st.subheader("📋 Included Templates")
for template in templates:
    st.markdown(f"- 📄 **{template}**")

st.divider()

st.info("""
ℹ️ Tip:  
- If your file does not have a 'Status' column, RateZap will auto-detect occupancy based on Check-in/Check-out dates.  
- You can leave optional fields empty in Comprehensive Guest Format.
""")
