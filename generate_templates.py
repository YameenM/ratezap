from utils import hide_streamlit_ui
hide_streamlit_ui()
import pandas as pd
import zipfile
from io import BytesIO

# 📂 Define sample data for each format
files = {}

# 1. Standard Format.xlsx
standard_df = pd.DataFrame({
    "Room Type": ["Deluxe", "Suite"],
    "Status": ["Occupied", "Vacant"],
    "Rate": [100.0, 150.0],
    "Arrival Date": ["2025-04-25", "2025-04-20"],
    "Departure Date": ["2025-04-27", "2025-04-22"]
})
files['Standard Format.xlsx'] = standard_df

# 2. Hilton Format.xlsx
hilton_df = pd.DataFrame({
    "Type": ["Deluxe", "Standard"],
    "Status": ["Occupied", "Vacant"],
    "Tariff": [120.0, 80.0],
    "Arrival": ["2025-04-24", "2025-04-23"],
    "Departure": ["2025-04-26", "2025-04-24"]
})
files['Hilton Format.xlsx'] = hilton_df

# 3. Marriott Format.xlsx
marriott_df = pd.DataFrame({
    "Room Class": ["Executive", "Superior"],
    "Occupancy Status": ["Occupied", "Vacant"],
    "Rate Per Night": [200.0, 150.0],
    "Check-in": ["2025-04-25", "2025-04-20"],
    "Check-out": ["2025-04-28", "2025-04-21"]
})
files['Marriott Format.xlsx'] = marriott_df

# 4. Custom Minimal Format.xlsx
custom_minimal_df = pd.DataFrame({
    "Room Type": ["Deluxe", "Standard"],
    "Rate": [90.0, 70.0],
    "Check-In Date": ["2025-04-25", "2025-04-23"],
    "Check-Out Date": ["2025-04-27", "2025-04-24"]
})
files['Custom Minimal Format.xlsx'] = custom_minimal_df

# 5. Comprehensive Guest Format.xlsx
comprehensive_df = pd.DataFrame({
    "Guest Name": ["John Doe", "Ali Khan"],
    "Meal Plan": ["Breakfast", "Full Board"],
    "Room Type": ["Deluxe", "Executive"],
    "Check-In": ["2025-04-25", "2025-04-26"],
    "Check-Out": ["2025-04-27", "2025-04-28"],
    "Total Nights": [2, 2],
    "Company Name": ["Alpha Corp", "N/A"],
    "Nationality": ["USA", "Pakistan"]
})
files['Comprehensive Guest Format.xlsx'] = comprehensive_df

# 6. Sample Night Audit.csv
sample_night_audit_df = pd.DataFrame({
    "Room Type": ["Deluxe", "Suite"],
    "Status": ["Occupied", "Vacant"],
    "Rate": [100.0, 150.0],
    "Arrival": ["2025-04-25", "2025-04-20"],
    "Departure": ["2025-04-27", "2025-04-22"]
})
files['Sample Night Audit.csv'] = sample_night_audit_df

# 🎯 Create and save ZIP
with zipfile.ZipFile('RateZap_Sample_Import_Templates.zip', 'w') as zip_file:
    for filename, df in files.items():
        if filename.endswith('.xlsx'):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            zip_file.writestr(filename, buffer.getvalue())
        else:
            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            zip_file.writestr(filename, buffer.getvalue())

print("✅ RateZap_Sample_Import_Templates.zip created successfully!")
