import streamlit as st
import pandas as pd
import math
from datetime import datetime
from utils import hide_streamlit_ui
from helpers.night_audit_utils import save_audit_summary, convert_to_serializable

hide_streamlit_ui()

# ===============================================
# 🧠 Infer Occupied using Check-In and Check-Out dates
def ensure_status_column(df):
    today = pd.to_datetime("today").normalize()

    if 'Check-In Date' in df.columns and 'Check-Out Date' in df.columns:
        arrival = pd.to_datetime(df['Check-In Date'], errors='coerce')
        departure = pd.to_datetime(df['Check-Out Date'], errors='coerce')

        df['Occupied'] = ((arrival <= today) & (departure >= today)).astype(int)
        df['Occupied_Display'] = df['Occupied'].apply(lambda x: "👤 Occupied" if x == 1 else "🛏️ Vacant")
    else:
        raise ValueError("❌ Cannot calculate occupancy — missing Check-In/Out dates")

    return df

# ===============================================
# 🏨 Standard Format
def parse_standard_audit(df, symbol):
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

    if math.isnan(adr): adr = 0.0
    if math.isnan(avg_rate): avg_rate = 0.0

    room_summary_df = df.groupby("Room Type").agg(
        Total_Rooms=('Room Type', 'count'),
        Occupied_Rooms=('Occupied', 'sum'),
        Average_Rate=('Rate', 'mean')
    ).reset_index()

    # ✅ Summary
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

# ===============================================
# 🔄 Custom Format
def parse_custom_audit(df, symbol):
    st.markdown("#### ⚙️ Column Mapping")
    columns = df.columns.tolist()
    room_type_col = st.selectbox("🔹 Room Type column", columns)
    rate_col = st.selectbox("🔹 Rate column", columns)
    checkin_col = st.selectbox("🔹 Check-In Date column", columns)
    checkout_col = st.selectbox("🔹 Check-Out Date column", columns)

    excluded = [room_type_col, rate_col, checkin_col, checkout_col]
    extra_cols = [col for col in columns if col not in excluded]
    selected_extra_cols = st.multiselect("➕ Optional Extra Columns", extra_cols)

    # Convert timestamps
    checkin_raw = pd.to_numeric(df[checkin_col], errors="coerce")
    checkout_raw = pd.to_numeric(df[checkout_col], errors="coerce")

    def convert_timestamp(series):
        if series.max() > 1e15:
            return pd.to_datetime(series, unit="ns", errors="coerce")
        elif series.max() > 1e12:
            return pd.to_datetime(series, unit="ms", errors="coerce")
        elif series.max() > 1e10:
            return pd.to_datetime(series, unit="s", errors="coerce")
        return pd.to_datetime(series, errors="coerce")

    checkin_converted = convert_timestamp(checkin_raw)
    checkout_converted = convert_timestamp(checkout_raw)

    mapped_df = pd.DataFrame({
        "Room Type": df[room_type_col],
        "Rate": df[rate_col],
        "Check-In Date": checkin_converted,
        "Check-Out Date": checkout_converted
    })

    for col in selected_extra_cols:
        mapped_df[col] = df[col]

    return parse_standard_audit(mapped_df, symbol)

# ===============================================
# 🏨 Marriott Format
def parse_marriott_audit(df, symbol):
    df.rename(columns={
        "Room_Category": "Room Type",
        "Rate_USD": "Rate",
        "In_Date": "Check-In Date",
        "Out_Date": "Check-Out Date"
    }, inplace=True)

    df = ensure_status_column(df)
    return parse_standard_audit(df, symbol)

# ===============================================
# 🏨 Hilton Format
def parse_hilton_audit(df, symbol):
    df.rename(columns={
        "Type": "Room Type",
        "Tariff": "Rate",
        "Arrival": "Check-In Date",
        "Departure": "Check-Out Date"
    }, inplace=True)

    df = ensure_status_column(df)
    return parse_standard_audit(df, symbol)
