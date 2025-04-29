import streamlit as st
from utils import hide_streamlit_ui
hide_streamlit_ui()

def display_ota_links_inline(hotel_name, city):
    st.markdown("### 🌐 OTA Comparison Links")

    query = f"{hotel_name} {city}".replace(" ", "+")
    ota_links = {
        "Booking.com": f"https://www.booking.com/searchresults.html?ss={query}",
        "Expedia": f"https://www.expedia.com/Hotel-Search?destination={query}",
        "Hotels.com": f"https://www.hotels.com/search.do?destination={query}",
        "Agoda": f"https://www.agoda.com/search?city={query}",
    }

    # Important: No indent inside HTML string!
    button_html = """
<div style='display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;'>
"""
    for name, link in ota_links.items():
        button_html += f"""<a href="{link}" target="_blank" style="
    background-color: #1f77b4;
    color: white;
    padding: 6px 14px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 14px;
">{name}</a>
"""

    button_html += "</div>"

    st.markdown(button_html, unsafe_allow_html=True)
