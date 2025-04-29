
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import json
from helpers.NightAuditParser import (
    parse_standard_audit,
    parse_custom_audit,
    parse_hilton_audit,
    parse_marriott_audit
)
from helpers.night_audit_utils import save_audit_summary, convert_to_serializable, send_night_audit_email
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import altair as alt
# Hide Streamlit sidebar completely
from utils import hide_streamlit_ui

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
    <h1 style='text-align: center; margin-bottom: 40px; font-size: 36px; color: #39FF14;'>
         🛏️ Night Audit
    </h1>
""", unsafe_allow_html=True)


# 🔒 Require Login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("Home.py")
    st.stop()

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



# Initialize safe empty variables
summary_data = {}
room_summary_df = pd.DataFrame()
extra_fields_df = pd.DataFrame()


# Setup DB
db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"
user_id = st.session_state["user"]["id"]
hotel_name = st.session_state.get("custom_data", {}).get("prop_name", "Hotel")

    
col1, col2 = st.columns([6, 1])
with col1:
    st.title("🧾 Night Audit Upload & Analysis")
    st.page_link("pages/DownloadTemplates.py", label="📂 Sample Templates 👉 Click Here ")


# 📤 Upload file
uploaded_file = st.file_uploader("Upload your Night Audit Excel file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    try:
        file_ext = uploaded_file.name.lower().split(".")[-1]

        template_type = st.selectbox("📄 Select Template Format", [
            "Standard Format", "Marriott Format", "Hilton Format", "Custom Format"
        ])

        # ✅ Read uploaded file
        if file_ext == "csv":
            df = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📑 Select Sheet", sheet_names) if len(sheet_names) > 1 else sheet_names[0]
            df = xls.parse(selected_sheet)
            
        file_ready = False  # default
            
        # 🔄 Auto-fix common columns
        rename_map = {
            "Arrival Date": "Check-In Date",
            "Departure Date": "Check-Out Date",
            "Status": "Occupied"
        }
        df.rename(columns=rename_map, inplace=True)


        # ✅ Auto-fix CheckIn / CheckOut if corrupted
        for col in ["CheckIn", "CheckOut"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if df[col].max() > 1e15:
                    df[col] = pd.to_datetime(df[col], unit="ns", errors="coerce")
                elif df[col].max() > 1e12:
                    df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce")
                elif df[col].max() > 1e10:
                    df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")
                else:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        # ✅ Auto-rename columns if needed
        rename_map = {
            "RoomType": "Room Type",
            "Status": "Occupied"
        }
        df.rename(columns=rename_map, inplace=True)

        # ✅ Convert Occupied field
        if "Occupied" in df.columns:
            df["Occupied"] = df["Occupied"].apply(lambda x: "👤 Occupied" if x == 1 else "🛏️ Vacant")

        # 📋 Show styled raw preview
        st.markdown("#### 🔍 Raw Preview")
        
        st.markdown("""
            <style>
            tbody tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            thead tr th {
                background-color: #003366;
                color: white;
                font-size: 16px;
                text-align: center;
            }
            tbody td {
                font-size: 15px;
                text-align: center;
            }
            </style>
        """, unsafe_allow_html=True)


        def color_occupied(val):
            if isinstance(val, str):
                return 'background-color: lightgreen' if "Occupied" in val else 'background-color: lightcoral'
            return ''

        if "Occupied" in df.columns:
            styled_df = df.style.applymap(color_occupied, subset=["Occupied"])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
        
          
        # 📋 📋 📋 File Ready Check
        st.divider()
        st.markdown("### 🛫 File Readiness Check")

        required_columns = ["Room Type", "Rate", "Check-In Date", "Check-Out Date"]

        # Check for missing columns
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"❌ File is missing important columns: {', '.join(missing_cols)}")
            st.warning("⚠️ Please fix your file or map the correct columns before proceeding to Analyze.")
        else:
            st.success("✅ File Ready! All required columns found. You can safely proceed to Analyze.")
            
            # ➡️ Show Analyze Button only if ready
            proceed = st.button("☑️ Confirm & Analyze 👍", use_container_width=True, key="analyze_confirm_button")

            if not proceed:
                st.stop()

        
        # 📋 Currency setup
        currency_symbol_map = {
            "$": "$", "AED": "AED", "PKR": "Rs", "₹": "₹", "€": "€", "£": "£", "CAD": "C$", "AUD": "A$"
        }
        currency_code = st.session_state.get("custom_data", {}).get("currency", "PKR")
        symbol = currency_symbol_map.get(currency_code, currency_code)

        audit_date = datetime.today().strftime('%Y-%m-%d')

        # ✅ Parsing based on Template
        st.info(f"Parsing using **{template_type}**...")
        result = None

        if template_type == "Standard Format":
            result = parse_standard_audit(df, symbol)
        elif template_type == "Marriott Format":
            result = parse_marriott_audit(df, symbol)
        elif template_type == "Hilton Format":
            result = parse_hilton_audit(df, symbol)
        elif template_type == "Custom Format":
            st.info("Please map the columns below.")
            result = parse_custom_audit(df, symbol)

        if result is None:
            st.warning("⚠️ Parsing failed. Please check your file or use Custom Format.")
            st.stop()

        occupancy, adr, summary_data, room_summary_df, extra_fields_df = result

        summary_data = convert_to_serializable(summary_data)

        extra_data = None
        if extra_fields_df is not None:
            extra_data = convert_to_serializable(extra_fields_df.to_dict(orient="records"))

        room_breakdown_json = None
        if room_summary_df is not None and not room_summary_df.empty:
            room_breakdown_json = room_summary_df.to_json(orient="records")

        # ✅ Save to DB
        save_audit_summary(
            user_id=user_id,
            audit_date=audit_date,
            occupancy_pct=occupancy,
            adr=adr,
            summary_dict=summary_data,
            extra_data=extra_data,
            hotel_name=hotel_name,
            room_breakdown_json=room_breakdown_json
        )

        now = datetime.now()
        formatted_time = now.strftime("%I:%M %p")
        formatted_date = now.strftime("%B %d, %Y")

        st.success(f"✅ Night Audit for **{hotel_name}** saved successfully at **{formatted_time}** on **{formatted_date}**! 🎉")
        
        # ✅ Summary Card + Buttons + Charts
        try:
            total_rooms = summary_data.get("Total_Rooms", 0)
            occupied_rooms = summary_data.get("Occupied", 0)
            vacant_rooms = summary_data.get("Vacant", 0)
            adr_value = summary_data.get("ADR", 0)
            if pd.isna(adr_value):
                adr_value = 0.0
            # 🎯 Optionally send email
            user_email = st.session_state["user"]["email"]
            full_name = st.session_state["user"]["full_name"]

            try:
                send_night_audit_email(
                    user_email=user_email,
                    full_name=full_name,
                    hotel_name=hotel_name,
                    total_rooms=total_rooms,
                    occupied=occupied_rooms,
                    vacant=vacant_rooms,
                    adr=adr,
                    symbol=symbol
                )
                st.success("📧 Confirmation email sent successfully!")
            except Exception as e:
                st.warning(f"⚠️ Audit saved, but failed to send confirmation email: {e}")


            occupancy_pct = int((occupied_rooms / total_rooms) * 100) if total_rooms else 0

            audit_date_friendly = datetime.today().strftime("%B %d, %Y")

            card_color = "#f0f2f6" if st.get_option("theme.base") == "light" else "#262730"
            text_color = "#000" if st.get_option("theme.base") == "light" else "#fff"
            
            # 🎯 Human-readable occupancy advice
            if occupancy_pct >= 70:
                st.success(f"👏 Great job! High occupancy today at {occupancy_pct}%.")
            elif occupancy_pct >= 40:
                st.info(f"👍 Moderate occupancy: {occupancy_pct}%. Keep pushing promotions.")
            else:
                st.warning(f"🙁 Low occupancy today at {occupancy_pct}%. Consider running special offers.")
                
                            # 💵 Smart ADR Insight (based on currency)

                currency_thresholds = {
                    "Rs": 10000,  # PKR
                    "AED": 500,   # UAE Dirham
                    "₹": 5000,    # Indian Rupees
                    "€": 150,     # Euro
                    "£": 150,     # British Pound
                    "C$": 200,    # Canadian Dollar
                    "A$": 200,    # Australian Dollar
                    "$": 200      # US Dollar
                }

                # Get threshold based on currency symbol
                threshold = currency_thresholds.get(symbol, 200)  # Default fallback 200

                # Show smart message based on ADR
                if adr_value > threshold:
                    st.success(f"💵 Strong ADR at {symbol}{adr_value:,.2f}. Well done!")
                elif adr_value > (threshold * 0.7):
                    st.info(f"📈 Decent ADR at {symbol}{adr_value:,.2f}. Room for improvement.")
                else:
                    st.warning(f"🔔 ADR is slightly low ({symbol}{adr_value:,.2f}). Review your pricing strategies.")



            # ➡️ Room type % calculation
            room_type_distribution = ""
            if room_summary_df is not None and not room_summary_df.empty:
                pie_df = room_summary_df.copy()
                total_rooms_count = pie_df["Total_Rooms"].sum()
                pie_df["Percentage"] = pie_df["Total_Rooms"] / total_rooms_count * 100
                room_type_distribution = "\n".join([
                    f"• {row['Room Type']}: {row['Percentage']:.1f}%"
                    for _, row in pie_df.iterrows()
                ])

            with st.container():
                st.markdown(f"""
                <div style="background-color: {card_color}; padding: 20px; margin-bottom: 20px; border-radius: 12px; margin-top: 20px; color: {text_color};">
                    <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
                        <div style="flex: 1; min-width: 250px;">
                            <h3>🏨 {hotel_name}</h3>
                            <p><strong>📅 Audit Date:</strong> {audit_date_friendly}</p>
                            <p><strong>🛏️ Total Rooms:</strong> {total_rooms}</p>
                            <p><strong>👤 Occupied Rooms:</strong> {occupied_rooms}</p>
                            <p><strong>📈 Occupancy:</strong> {occupancy_pct}%</p>
                            <p><strong>💵 ADR:</strong> {symbol}{adr_value:,.2f}</p>
                        </div>
                        <div style="flex: 1; min-width: 250px; padding-left: 40px;">
                            <h4>📊 Room Type Distribution:</h4>
                            <p style="white-space: pre-line;">{room_type_distribution}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 📄 Save Summary as PDF Button
            def generate_summary_pdf(hotel_name, audit_date, total_rooms, occupied_rooms, occupancy_pct, adr_value, symbol):
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                elements = []

                elements.append(Paragraph(f"🏨 {hotel_name}", styles['Title']))
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"📅 Audit Date: {audit_date}", styles['Normal']))
                elements.append(Paragraph(f"🛏️ Total Rooms: {total_rooms}", styles['Normal']))
                elements.append(Paragraph(f"💤 Occupied Rooms: {occupied_rooms}", styles['Normal']))
                elements.append(Paragraph(f"📈 Occupancy: {occupancy_pct}%", styles['Normal']))
                elements.append(Paragraph(f"💵 ADR: {symbol}{adr_value:,.2f}", styles['Normal']))

                doc.build(elements)
                pdf = buffer.getvalue()
                buffer.close()
                return pdf

            pdf_data = generate_summary_pdf(hotel_name, audit_date_friendly, total_rooms, occupied_rooms, occupancy_pct, adr_value, symbol)
            st.divider()

        
            colb1, colb2 = st.columns(2)

            with colb1:
                st.download_button(
                    label="📄 Download Last Uploaded Audit (PDF)",
                    data=pdf_data,
                    file_name=f"Audit_Summary_{hotel_name.replace(' ', '_')}_{audit_date_friendly.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with colb2:
                st.download_button(
                    label="📄 Save Summary as PDF",
                    data=pdf_data,
                    file_name=f"Audit_Summary_{hotel_name.replace(' ', '_')}_{audit_date_friendly.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            # 📈 Occupied vs Vacant Bar Chart
            if total_rooms > 0:
                st.markdown("#### 🏨 Occupied vs Vacant Rooms")
                occ_data = pd.DataFrame({
                    'Status': ['Occupied', 'Vacant'],
                    'Rooms': [occupied_rooms, vacant_rooms]
                })
                bar_chart = alt.Chart(occ_data).mark_bar(size=50).encode(
                    x=alt.X('Status', axis=alt.Axis(labelAngle=0)),
                    y='Rooms',
                    color=alt.Color('Status', scale=alt.Scale(domain=['Occupied', 'Vacant'], range=['seagreen', 'orangered'])),
                    tooltip=["Status", "Rooms"]
                ).properties(width=400, height=300)
                st.altair_chart(bar_chart, use_container_width=True)

            # 🥧 Room Type Pie Chart
            if room_summary_df is not None and not room_summary_df.empty:
                st.markdown("#### 🥧 Room Type Distribution")
                pie_df = room_summary_df.copy()
                pie_df.rename(columns={"Total_Rooms": "Rooms"}, inplace=True)
                chart = alt.Chart(pie_df).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Rooms", type="quantitative"),
                    color=alt.Color(field="Room Type", type="nominal"),
                    tooltip=["Room Type", "Rooms"]
                ).properties(width=400, height=300)
                st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.warning(f"⚠️ Error showing summary: {e}")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

else:
    st.info("📥 Please upload an Excel or CSV file to begin.")
    
# 🔥 7-Day Occupancy % and ADR Trend
st.markdown("#### 📈 Last 7 Audits Trend (Occupancy % & ADR)")

conn = sqlite3.connect(db_path)
query = """
    SELECT date AS audit_date, occupancy AS occupancy_pct, adr
    FROM night_audit_history
    WHERE user_id = ?
    ORDER BY date DESC
    LIMIT 7
"""
trend_df = pd.read_sql_query(query, conn, params=(user_id,))
conn.close()

if not trend_df.empty:
    trend_df["audit_date"] = pd.to_datetime(trend_df["audit_date"])
    trend_df = trend_df.sort_values("audit_date")

    base = alt.Chart(trend_df).encode(x=alt.X('audit_date:T', title='Date'))

    occupancy_line = base.mark_line(strokeWidth=3, color="seagreen").encode(
        y=alt.Y('occupancy_pct:Q', title='Occupancy %'),
        tooltip=["audit_date", "occupancy_pct"]
    )

    adr_line = base.mark_line(strokeWidth=3, color="orange").encode(
        y=alt.Y('adr:Q', title='ADR'),
        tooltip=["audit_date", "adr"]
    )

    trend_chart = alt.layer(occupancy_line, adr_line).resolve_scale(
        y = 'independent'  # Separate left/right axes
    ).properties(width=700, height=400)

    st.altair_chart(trend_chart, use_container_width=True)
else:
    st.info("ℹ️ Not enough past audits to show trend yet.")
