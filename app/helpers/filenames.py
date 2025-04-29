
from app.utils import hide_streamlit_ui
hide_streamlit_ui()
from datetime import datetime

def generate_export_filenames(prefix="report", extension="pdf", hotel_name=None):
    today_str = datetime.now().strftime("%Y-%m-%d")
    base = hotel_name or "hotel"
    safe_name = base.replace(" ", "_").lower()
    filename = f"{safe_name}_{prefix}_{today_str}.{extension}"
    return filename
