
import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from app.helpers.companies import generate_company_code

# ========== Setup ==========
st.set_page_config(page_title="Annual Rates | RateZap", layout="wide")
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
    <h1 style='text-align: center; margin-bottom: 40px;font-size: 36px; color: #39FF14;'>
         📄 Annual Rates
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


# ========== Constants ==========
MEAL_PLAN_OPTIONS = [
    "No Meals", "Breakfast", "Lunch", "Dinner",
    "Half-Board", "Full-Board", "All-Inclusive"
]
currency_symbols = {
    "$": "$", "AED": "AED", "PKR": "Rs", "₹": "₹", "€": "€",
    "£": "£", "CAD": "C$", "AUD": "A$"
}

# ========== Database ==========
conn = sqlite3.connect("ratezap.db", check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS annual_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    company_name TEXT,
    company_code TEXT,
    from_date TEXT,
    to_date TEXT,
    room_type TEXT,
    meal_plan TEXT,
    daily_rate REAL,
    weekend_rate REAL,
    holiday_rate REAL,
    notes TEXT,
    created_at TEXT
)""")
conn.commit()

c.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    company_code TEXT NOT NULL,
    created_at TEXT,
    UNIQUE(user_id, company_name),
    UNIQUE(user_id, company_code)
)
""")


# ========== Session Setup ==========
if "rate_blocks" not in st.session_state:
    st.session_state["rate_blocks"] = []
if "room_types" not in st.session_state:
    st.session_state["room_types"] = ["Standard", "Deluxe", "Suite"]
if "recently_deleted" not in st.session_state:
    st.session_state["recently_deleted"] = None
if "editing_block_id" not in st.session_state:
    st.session_state["editing_block_id"] = None

user = st.session_state.get("user", {})
custom_data = st.session_state.get("custom_data", {})
user_id = user.get("id", 1)
hotel_name = custom_data.get("prop_name", "Unnamed Hotel")
city = custom_data.get("city", "Unknown City")
country = custom_data.get("country", "Unknown Country")
currency = custom_data.get("currency", "USD")
currency_symbol = currency_symbols.get(currency, currency)

st.title("📄 Annual Rate Planner")
st.markdown(f"**🏨 Hotel:** {hotel_name} | 📍 {city}, {country} | 💱 Currency: {currency_symbol}")

date_format = st.selectbox(
    "🌍 Date Format Preference", [
        ("%b-%d-%Y", "USA (MM-DD-YYYY)"),
        ("%d-%b-%Y", "Pakistan/India/Middle East (DD-MM-YYYY)"),
        ("%d/%b/%Y", "Europe/UK (DD/MM/YYYY)")
    ],
    format_func=lambda x: x[1]
)[0]

# ========== Manage Companies ==========
st.markdown("##### ✈️ Manage Tour Operator / Company")
companies = [row[0] for row in c.execute("SELECT company_name FROM companies WHERE user_id = ?", (user_id,))]
st.session_state["companies"] = companies

col1, col2 = st.columns(2)
with col1:
    new_company = st.text_input("➕ Add Company")
    if st.button("Add Company"):
        name = new_company.strip().title()
        if name and name not in companies:
            company_code = generate_company_code(name, user_id, conn)
            st.success(f"✅ Added company: {name} ({company_code})")
            st.rerun()

with col2:
    if companies:
        company_to_remove = st.selectbox("➖ Remove Company", companies)
        if st.button("Remove Company"):
            c.execute("DELETE FROM companies WHERE user_id = ? AND company_name = ?", (user_id, company_to_remove))
            conn.commit()
            st.success(f"🗑️ Removed company: {company_to_remove}")
            st.rerun()

# ========== Manage Room Types ==========
st.markdown("##### 🏘️ Manage Room Types")
col1, col2 = st.columns(2)
with col1:
    new_room = st.text_input("➕ Add Room Type")
    if st.button("Add Room Type"):
        if new_room and new_room not in st.session_state["room_types"]:
            st.session_state["room_types"].append(new_room)
            st.success(f"✅ Added room type: {new_room}")
with col2:
    if st.session_state["room_types"]:
        room_to_remove = st.selectbox("➖ Remove Room Type", st.session_state["room_types"])
        if st.button("Remove Room Type"):
            st.session_state["room_types"].remove(room_to_remove)
            st.success(f"🗑️ Removed room type: {room_to_remove}")
            
#=============================================Generate PDF===========================================

def generate_company_pdf(hotel_name, city, country, company_name, generated_by, rates_data, notes_data, meal_plan_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1
    normal_style = styles['Normal']

    note_style = ParagraphStyle(
    name="NoteStyle",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.gray,
    leftIndent=2,
    rightIndent=2,
    spaceBefore=2,
    spaceAfter=2,
    italic=True,
    alignment=0,  # Left
    wordWrap='CJK'  # Wrap long text automatically
)


    # 🏨 Hotel Title
    title_text = f"~ {hotel_name} | {city} | {country} ~"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 12))

    # 📋 Company Info (Left-Right)
    company_table = Table(
        [[
            Paragraph(f"<b>Company:</b> {company_name}", normal_style),
            Paragraph(f"<b>Generated by:</b> {generated_by}", normal_style)
        ]],
        colWidths=[doc.width/2.0, doc.width/2.0]
    )
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 12))

    # 🥣 Meal Plan Explanation
    elements.append(Paragraph(meal_plan_text, normal_style))
    elements.append(Spacer(1, 12))

    # 📑 Common Table Column Widths
    col_widths = [doc.width/7.0] * 7

    # 📑 Table Header
    table_header = [['From', 'To', 'Room Type', 'Meal Plan', 'Daily Rate', 'Weekend Rate', 'Holiday Rate']]
    header_table = Table(table_header, colWidths=col_widths, hAlign='CENTER')
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    elements.append(header_table)

    # 📑 Loop through each rate block separately
    for idx, rate in enumerate(rates_data):
        # 🦓 Set background color based on row index (even/odd)
        background_color = colors.whitesmoke if idx % 2 else colors.HexColor("#ffffff")

        rate_table = Table([rate], colWidths=col_widths, hAlign='CENTER')
        rate_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), background_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ]))
        elements.append(rate_table)

        # 📝 Show Note immediately under block (if exists)
        note_text = notes_data[idx]
        if note_text.strip():
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(f"<b>Note:</b> {note_text}", note_style))
            elements.append(Spacer(1, 6))
        else:
            elements.append(Spacer(1, 6))

    # 📄 Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf



# ========== Add Rate Block ==========
st.markdown("### ➕ Add New Rate Block")
if st.session_state.get("rate_blocks"):
    last_block = st.session_state["rate_blocks"][-1]
    if st.button("📋 Copy Last Block"):
        st.session_state["prefill_block"] = last_block
else:
    st.session_state["prefill_block"] = {}

with st.form("rate_block_form", clear_on_submit=True):
        # Inside your form "rate_block_form"
    from_date = st.date_input(
        "From Date", 
        value=pd.to_datetime(st.session_state.get("prefill_block", {}).get("from_date", date.today()))
    )
    to_date = st.date_input(
        "To Date", 
        value=pd.to_datetime(st.session_state.get("prefill_block", {}).get("to_date", date.today()))
    )
    room_type = st.selectbox(
        "Room Type", 
        st.session_state["room_types"],
        index=st.session_state["room_types"].index(
            st.session_state.get("prefill_block", {}).get("room_type", st.session_state["room_types"][0])
        ) if st.session_state.get("prefill_block", {}).get("room_type") in st.session_state["room_types"] else 0
    )
    meal_plan = st.selectbox(
        "Meal Plan", 
        MEAL_PLAN_OPTIONS,
        index=MEAL_PLAN_OPTIONS.index(
            st.session_state.get("prefill_block", {}).get("meal_plan", MEAL_PLAN_OPTIONS[0])
        ) if st.session_state.get("prefill_block", {}).get("meal_plan") in MEAL_PLAN_OPTIONS else 0
    )
    company_name = st.selectbox(
        "Tour Operator / Company", 
        st.session_state["companies"],
        index=st.session_state["companies"].index(
            st.session_state.get("prefill_block", {}).get("company_name", st.session_state["companies"][0])
        ) if st.session_state.get("prefill_block", {}).get("company_name") in st.session_state["companies"] else 0
    )
    daily_rate = st.number_input(
        "Daily Rate", 
        min_value=0, 
        value=st.session_state.get("prefill_block", {}).get("daily_rate", 0)
    )
    weekend_rate = st.number_input(
        "Weekend Rate", 
        min_value=0, 
        value=st.session_state.get("prefill_block", {}).get("weekend_rate", 0)
    )
    holiday_rate = st.number_input(
        "Holiday Rate", 
        min_value=0, 
        value=st.session_state.get("prefill_block", {}).get("holiday_rate", 0)
    )
    notes = st.text_area(
        "Notes", 
        placeholder="Optional special notes...",
        value=st.session_state.get("prefill_block", {}).get("notes", "")
    )


    submitted = st.form_submit_button("➕ Add Rate Block")
    if submitted:
        company_code = generate_company_code(company_name, user_id, conn)
        c.execute("""INSERT INTO annual_rates (
            user_id, company_name, company_code, from_date, to_date,
            room_type, meal_plan, daily_rate, weekend_rate, holiday_rate, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            user_id, company_name, company_code,
            from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"),
            room_type, meal_plan, daily_rate, weekend_rate, holiday_rate, notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        st.session_state["rate_blocks"].append({
            "from_date": from_date,
            "to_date": to_date,
            "room_type": room_type,
            "meal_plan": meal_plan,
            "company_name": company_name,
            "daily_rate": daily_rate,
            "weekend_rate": weekend_rate,
            "holiday_rate": holiday_rate,
            "notes": notes
        })
        st.success("✅ Rate Block added successfully!")
        st.rerun()
        st.session_state["prefill_block"] = {}


# [..continues with Edit, Delete, Preview sections exactly same..]
# ====================== Manage Existing Rate Blocks ======================
st.markdown("### 🧹 Manage Saved Rate Blocks")

if "editing_block_id" not in st.session_state:
    st.session_state["editing_block_id"] = None

db_blocks = pd.read_sql_query("""
    SELECT id, from_date, to_date, room_type, meal_plan, daily_rate, weekend_rate, holiday_rate,
           company_name, company_code, notes, created_at
    FROM annual_rates
    WHERE user_id = ?
    ORDER BY from_date ASC
""", conn, params=(user_id,))

if db_blocks.empty:
    st.info("ℹ️ No saved rate blocks to manage.")
else:
    for idx, row in db_blocks.iterrows():
        block_info = f"{row['from_date']} → {row['to_date']} | {row['room_type']} | {row['meal_plan']} | {currency_symbol}{row['daily_rate']} | {row['company_name']}"

        with st.expander(block_info):
            edit_col1, edit_col2 = st.columns([2, 1])
            with edit_col1:
                if st.button("✏️ Edit", key=f"edit_block_{row['id']}"):
                    st.session_state["editing_block_id"] = row["id"]
            with edit_col2:
                if st.button("🗑️ Delete", key=f"delete_block_{row['id']}"):
                    c.execute("DELETE FROM annual_rates WHERE id = ?", (row["id"],))
                    conn.commit()
                    st.success("✅ Block deleted successfully.")
                    st.rerun()

            # If editing
            if st.session_state.get("editing_block_id") == row["id"]:
                st.markdown("---")
                st.markdown("**🛠️ Edit this Block**")
                from_date = st.date_input("From Date", value=pd.to_datetime(row["from_date"]))
                to_date = st.date_input("To Date", value=pd.to_datetime(row["to_date"]))
                room_type = st.text_input("Room Type", value=row["room_type"])
                meal_plan = st.selectbox("Meal Plan", MEAL_PLAN_OPTIONS, index=MEAL_PLAN_OPTIONS.index(row["meal_plan"]) if row["meal_plan"] in MEAL_PLAN_OPTIONS else 0)
                daily_rate = st.number_input("Daily Rate", value=float(row["daily_rate"]))
                weekend_rate = st.number_input("Weekend Rate", value=float(row["weekend_rate"]))
                holiday_rate = st.number_input("Holiday Rate", value=float(row["holiday_rate"]))
                notes = st.text_area("Notes", value=row["notes"] if row["notes"] else "")

                if st.button("💾 Save Changes", key=f"save_block_{row['id']}"):
                    c.execute("""
                        UPDATE annual_rates
                        SET from_date = ?, to_date = ?, room_type = ?, meal_plan = ?, daily_rate = ?, weekend_rate = ?, holiday_rate = ?, notes = ?
                        WHERE id = ?
                    """, (
                        from_date.strftime("%Y-%m-%d"),
                        to_date.strftime("%Y-%m-%d"),
                        room_type,
                        meal_plan,
                        daily_rate,
                        weekend_rate,
                        holiday_rate,
                        notes,
                        row["id"]
                    ))
                    conn.commit()
                    st.success("✅ Block updated successfully!")
                    st.session_state["editing_block_id"] = None
                    st.rerun()

# =================== Undo Deletion ======================
if "recently_deleted" in st.session_state and st.session_state.get("recently_deleted"):
    with st.expander("♻️ Undo Last Deletion", expanded=True):
        deleted = st.session_state["recently_deleted"]
        st.write(f"Recently deleted: **{deleted['room_type']} | {deleted['meal_plan']} | {deleted['company_name']}** from {deleted['from_date']} to {deleted['to_date']}")

        if st.button("🔄 Restore This Block"):
            c.execute("""
                INSERT INTO annual_rates (
                    user_id, company_name, company_code, from_date, to_date,
                    room_type, meal_plan, daily_rate, weekend_rate, holiday_rate, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                deleted["company_name"],
                deleted["company_code"],
                deleted["from_date"],
                deleted["to_date"],
                deleted["room_type"],
                deleted["meal_plan"],
                deleted["daily_rate"],
                deleted["weekend_rate"],
                deleted["holiday_rate"],
                deleted["notes"],
                deleted["created_at"]
            ))
            conn.commit()
            st.success("✅ Block restored successfully!")
            st.session_state["recently_deleted"] = None
            st.rerun()

# =================== Search & Preview =====================
st.markdown("### 🔍 Search Company Rates")

company_query = st.text_input("Enter Company Name or Code")

if st.button("👁️ Rate Preview"):
    if not company_query.strip():
        st.warning("⚠️ Please enter a company name or code to preview rates.")
    else:
        query = """
            SELECT from_date, to_date, room_type, meal_plan, daily_rate, weekend_rate, holiday_rate,
                   company_name, company_code, notes, created_at
            FROM annual_rates
            WHERE user_id = ? AND (company_name LIKE ? OR company_code LIKE ?)
            ORDER BY from_date ASC

        """
        like_query = f"%{company_query}%"
        result = pd.read_sql_query(query, conn, params=(user_id, like_query, like_query))

        if not result.empty:
            actual_company_name = result["company_name"].iloc[0]
            # 🔥 Sort results naturally by From Date
            
            result["from_date"] = pd.to_datetime(result["from_date"])
            result = result.sort_values(by="from_date").reset_index(drop=True)
            
            # Format rates properly for preview
            for col in ["daily_rate", "weekend_rate", "holiday_rate"]:
                result[col] = result[col].apply(
                    lambda x: f"{currency_symbol}{float(x):,.2f}" if isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit() else x
                )

            result["from_date"] = pd.to_datetime(result["from_date"]).dt.strftime(date_format)
            result["to_date"] = pd.to_datetime(result["to_date"]).dt.strftime(date_format)

            st.markdown(f"### 📄 Rate Preview for `{actual_company_name}`")
            st.dataframe(
                result[["from_date", "to_date", "room_type", "meal_plan", "daily_rate", "weekend_rate", "holiday_rate", "company_name", "company_code", "notes", "created_at"]],
                use_container_width=True,
                height=600
            )
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



            # ========================= Prepare rates_list properly =========================
            rates_list = []
            notes_list = []
            for idx, row in result.iterrows():
                rates_list.append([
                    row['from_date'],
                    row['to_date'],
                    row['room_type'],
                    row['meal_plan'],
                    row['daily_rate'],
                    row['weekend_rate'],
                    row['holiday_rate']
                ])
                notes_list.append(row['notes'] if pd.notna(row['notes']) else "")

            # ✍️ Meal Plan text
            meal_plan_text = """
            <b>Meal Plan Explanation:</b><br/>
            • No Meals = No Meals Included<br/>
            • Breakfast = Breakfast Only<br/>
            • Lunch = Lunch Only<br/>
            • Dinner = Dinner Only<br/>
            • Half-Board (L) = Breakfast + Lunch<br/>
            • Half-Board (D) = Breakfast + Dinner<br/>
            • Full-Board = Breakfast + Lunch + Dinner<br/>
            • All-Inclusive = All Meals + Tea/Coffee/Soft Drinks
            """
            with st.expander("ℹ️ Meal Plan Explanation"):
                st.markdown(meal_plan_text, unsafe_allow_html=True)


            # ✍️ Note text
            note_text = """
            <b>NOTE:</b><br/>
            • Above rates are net, non-commissionable unless otherwise specified.<br/>
            • Rates are subject to hotel policy and availability.<br/>
            • Check-in Time: 2:00 PM / Check-out Time: 12:00 Noon.<br/>
            • Peak Season surcharges may apply.
            """

            # 📄 Correct call to generate_company_pdf
            pdf_data = generate_company_pdf(
                hotel_name,
                city,
                country,
                actual_company_name,
                user.get("full_name", "Unknown User"),
                rates_list,
                notes_list,
                meal_plan_text
            )

            # 📥 Download Buttons
            col_csv, col_pdf = st.columns([2, 12])

            with col_csv:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=result.to_csv(index=False).encode("utf-8"),
                    file_name=f"{actual_company_name}_rates.csv",
                    mime="text/csv"
                )

            with col_pdf:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=f"{actual_company_name}_annual_rates.pdf",
                    mime="application/pdf"
                )

        else:
            st.warning("⚠️ No matching records found.")
