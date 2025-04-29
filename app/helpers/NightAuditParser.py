import streamlit as st
import pandas as pd
import math
from datetime import datetime
from app.utils import hide_streamlit_ui
from app.helpers.night_audit_utils import save_audit_summary, convert_to_serializable
hide_streamlit_ui()

def ensure_status_column(df):
    today = pd.to_datetime("today").normalize()

    if 'Status' not in df.columns and 'Occupied' not in df.columns:
        st.warning("⚠️ 'Status' column missing. Auto-detecting occupancy based on dates...")

        # Check possible Arrival/Departure or Check-In/Check-Out
        if 'Arrival Date' in df.columns and 'Departure Date' in df.columns:
            arrival = pd.to_datetime(df['Arrival Date'], errors='coerce')
            departure = pd.to_datetime(df['Departure Date'], errors='coerce')
        elif 'Check-In Date' in df.columns and 'Check-Out Date' in df.columns:
            arrival = pd.to_datetime(df['Check-In Date'], errors='coerce')
            departure = pd.to_datetime(df['Check-Out Date'], errors='coerce')
        else:
            raise ValueError("❌ Cannot auto-detect occupancy because missing columns: Arrival/Departure or Check-In/Check-Out")

        # Infer occupancy
        df['Occupied'] = ((arrival <= today) & (departure >= today)).apply(lambda x: 'Occupied' if x else 'Vacant')

    return df

#==============================================================

# 🏨 Standard Format
def parse_standard_audit(df, symbol):
    # 👇 Ensure Status column is available
    df = ensure_status_column(df)
    required_cols = ["Room Type", "Occupied", "Rate", "Check-In Date", "Check-Out Date"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return None, None, None, None, None

    df["Occupied"] = pd.to_numeric(df["Occupied"], errors="coerce")
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")

    total_rooms = int(len(df))
    occupied_rooms = int(df["Occupied"].sum())
    vacant_rooms = total_rooms - occupied_rooms
    
    if occupied_rooms == 0:
       st.warning("🛑 No occupied rooms found in this audit. ADR and Revenue are set to 0 by default.")

    avg_rate = df.loc[df["Occupied"] == 1, "Rate"].mean()
    total_revenue = df.loc[df["Occupied"] == 1, "Rate"].sum()
    adr = total_revenue / occupied_rooms if occupied_rooms else 0
    if math.isnan(adr):
       adr = 0.0
    if math.isnan(avg_rate):
       avg_rate = 0.0

    room_summary_df = df.groupby("Room Type").agg(
        Total_Rooms=('Room Type', 'count'),
        Occupied_Rooms=('Occupied', 'sum'),
        Average_Rate=('Rate', 'mean')
    ).reset_index()

    # ✅ Display success and summary nicely
    with st.container(border=True):
        st.success("✅ Night Audit uploaded and processed successfully!")

        col1, col2, col3 = st.columns(3)
        col1.metric("🏨 Total Rooms", f"{total_rooms}")
        col2.metric("👤 Occupied", f"{occupied_rooms}")
        col3.metric("🛌 Vacant", f"{vacant_rooms}")

        col1.metric("💵 Total Revenue", f"{symbol}{total_revenue:,.2f}")
        col2.metric("💲 Average Rate", f"{symbol}{avg_rate:,.2f}")
        col3.metric("📈 ADR", f"{symbol}{adr:,.2f}")

    st.divider()

    # 📊 Audit Summary DataFrame
    st.markdown("#### 📊 Room Type Summary")
    st.dataframe(room_summary_df, use_container_width=True)
    
    
    occupancy_pct = int((occupied_rooms / total_rooms) * 100) if total_rooms > 0 else 0

    audit_date = datetime.now().strftime("%Y-%m-%d")
    user_id = st.session_state["user"]["id"]
    hotel_name = st.session_state.get("custom_data", {}).get("prop_name", "Hotel")

    summary_data = {
        "Total_Rooms": total_rooms,
        "Occupied": occupied_rooms,
        "Vacant": vacant_rooms,
        "Revenue": total_revenue,
        "ADR": adr,
        "Average_Rate": avg_rate,
        "symbol": symbol
    }

    room_json = None
    if room_summary_df is not None and not room_summary_df.empty:
        room_json = room_summary_df.to_json(orient="records")

    save_audit_summary(
        user_id=user_id,
        audit_date=audit_date,
        occupancy_pct=occupancy_pct,
        adr=adr,
        summary_dict=convert_to_serializable(summary_data),
        hotel_name=hotel_name,
        room_breakdown_json=room_json
    )

    return occupancy_pct, adr, summary_data, room_summary_df, None

#=======================================================================================================
# 🔄 Custom Format
def parse_custom_audit(df, symbol):
    st.markdown("#### ⚙️ Column Mapping")
    columns = df.columns.tolist()
    room_type_col = st.selectbox("🔹 Room Type column", columns)
    occupied_col = st.selectbox("🔹 Occupied column", columns)
    rate_col = st.selectbox("🔹 Rate column", columns)
    checkin_col = st.selectbox("🔹 Check-In Date column", columns)
    checkout_col = st.selectbox("🔹 Check-Out Date column", columns)

    excluded = [room_type_col, occupied_col, rate_col, checkin_col, checkout_col]
    extra_cols = [col for col in columns if col not in excluded]
    selected_extra_cols = st.multiselect("➕ Optional Extra Columns", extra_cols)

    # Handle Checkin and Checkout columns
    checkin_raw = pd.to_numeric(df[checkin_col], errors="coerce")
    checkout_raw = pd.to_numeric(df[checkout_col], errors="coerce")

    def convert_timestamp(series):
        try:
            if series.max() > 1e15:
                dt_series = pd.to_datetime(series, unit="ns", errors="coerce")
            elif series.max() > 1e12:
                dt_series = pd.to_datetime(series, unit="ms", errors="coerce")
            elif series.max() > 1e10:
                dt_series = pd.to_datetime(series, unit="s", errors="coerce")
            else:
                dt_series = pd.to_datetime(series, errors="coerce")
        except Exception:
            dt_series = pd.to_datetime(series, errors="coerce")
        return dt_series

    checkin_converted = convert_timestamp(checkin_raw)
    checkout_converted = convert_timestamp(checkout_raw)

    # Apply user-chosen format
    date_format = st.radio("🗓️ Choose Date Format for Check-In/Out:", [
        "Original Timestamp", "YYYY-MM-DD", "DD-MM-YYYY", "MM-DD-YYYY"
    ], horizontal=True)

    if date_format == "YYYY-MM-DD":
        checkin_converted = checkin_converted.dt.strftime("%Y-%m-%d")
        checkout_converted = checkout_converted.dt.strftime("%Y-%m-%d")
    elif date_format == "DD-MM-YYYY":
        checkin_converted = checkin_converted.dt.strftime("%d-%m-%Y")
        checkout_converted = checkout_converted.dt.strftime("%d-%m-%Y")
    elif date_format == "MM-DD-YYYY":
        checkin_converted = checkin_converted.dt.strftime("%m-%d-%Y")
        checkout_converted = checkout_converted.dt.strftime("%m-%d-%Y")
    else:
        pass

    mapped_df = pd.DataFrame({
        "Room Type": df[room_type_col],
        "Occupied": df[occupied_col].apply(lambda x: 1 if str(x).strip().lower() == "occupied" else 0),
        "Rate": df[rate_col],
        "Check-In Date": checkin_converted,
        "Check-Out Date": checkout_converted
    })

    for col in selected_extra_cols:
        mapped_df[col] = df[col]

    return parse_standard_audit(mapped_df, symbol)


#===============================================================================================

# 🏨 Marriott Format
def parse_marriott_audit(df, symbol):
    required_cols = ["Room_Category", "Status", "Rate_USD", "In_Date", "Out_Date"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Marriott audit file is missing columns: {', '.join(missing_cols)}")

    mapped_df = pd.DataFrame({
        "Room Type": df["Room_Category"],
        "Occupied": df["Status"].apply(lambda x: 1 if str(x).strip().lower() == "occupied" else 0),
        "Rate": df["Rate_USD"],
        "Check-In Date": df["In_Date"],
        "Check-Out Date": df["Out_Date"]
    })

    return parse_standard_audit(mapped_df, symbol)

#=================================================================================

def parse_hilton_audit(df, symbol):
    required_cols = ["Type", "Tariff", "Arrival", "Departure"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Hilton audit file is missing columns: {', '.join(missing_cols)}")

    if "Status" in df.columns:
        occupied = df["Status"].apply(lambda x: 1 if str(x).strip().lower() == "occupied" else 0)
    else:
        today = pd.to_datetime("today").normalize()
        arrival = pd.to_datetime(df["Arrival"], errors="coerce")
        departure = pd.to_datetime(df["Departure"], errors="coerce")
        occupied = ((arrival <= today) & (departure >= today)).astype(int)

    mapped_df = pd.DataFrame({
        "Room Type": df["Type"],
        "Occupied": occupied,
        "Rate": df["Tariff"],
        "Check-In Date": df["Arrival"],
        "Check-Out Date": df["Departure"]
    })

    return parse_standard_audit(mapped_df, symbol)
