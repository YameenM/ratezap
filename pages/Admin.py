import streamlit as st
st.set_page_config(page_title="Admin Panel", layout="wide")
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib, random, string, os
from utils import hide_streamlit_ui
from io import BytesIO

hide_streamlit_ui()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return "@" in email and "." in email

def generate_reset_token(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 🔐 Restrict access to Admins only
if "user" not in st.session_state:
    st.warning("⚠️ Please log in first.")
    st.switch_page("pages/Home.py")
    st.stop()

if st.session_state["user"].get("subscription_status") != "admin":
    st.error("⛔ You do not have permission to access this page.")
    st.stop()

# 📦 Connect to database
db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

# 📊 Page title
st.markdown("""
    <h1 style='text-align:center; color:#1E90FF;'>🛠️ Admin Panel</h1>
    <hr>
""", unsafe_allow_html=True)

# 👑 Create New Admin User
st.markdown("### 👑 Add New Admin Account")

with st.form("create_admin_form"):
    new_admin_email = st.text_input("Admin Email")
    new_admin_password = st.text_input("Admin Password", type="password")
    new_admin_name = st.text_input("Full Name")

    submitted = st.form_submit_button("Create Admin")

    if submitted:
        if not new_admin_email or not new_admin_password or not new_admin_name:
            st.warning("Please fill in all fields.")
        elif not is_valid_email(new_admin_email):
            st.warning("Please enter a valid email address.")
        else:
            hashed_pw = hash_password(new_admin_password)
            try:
                c.execute("""
                    INSERT INTO users (full_name, email, password, subscription_status, trial_start)
                    VALUES (?, ?, ?, 'admin', ?)
                """, (new_admin_name, new_admin_email, hashed_pw, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"✅ Admin user {new_admin_email} created!")
            except sqlite3.IntegrityError:
                st.error("⚠️ This email is already registered.")

# 📈 Summary Metrics
c.execute("SELECT COUNT(*) FROM users")
total_users = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE subscription_status='trial'")
trial_users = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE subscription_status='active'")
paid_users = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE subscription_status='expired'")
expired_users = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE trial_start >= ?", (datetime.now() - timedelta(days=7),))
weekly_signups = c.fetchone()[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👥 Total Users", total_users)
col2.metric("🆓 Trials", trial_users)
col3.metric("💳 Paid", paid_users)
col4.metric("❌ Expired", expired_users)
col5.metric("📅 This Week", weekly_signups)

st.markdown("---")

# 👥 User Management
st.subheader("📋 User Accounts")

# Fetch users
c.execute("""
    SELECT id, full_name, email, trial_start, subscription_status, hotel_name, country
    FROM users
    ORDER BY id DESC
""")
user_data = c.fetchall()
user_df = pd.DataFrame(user_data, columns=["ID", "Name", "Email", "Trial Start", "Status", "Hotel", "Country"])

# Add trial expiry countdown and badge style
def style_status(row):
    color = {
        "trial": "orange",
        "active": "green",
        "expired": "red",
        "admin": "blue"
    }.get(row["Status"], "gray")
    return f"<span style='color:{color}; font-weight:bold;'>{row['Status'].capitalize()}</span>"

user_df["Trial Ends"] = user_df["Trial Start"].apply(lambda x: 
    (datetime.strptime(x, "%Y-%m-%d") + timedelta(days=7) - datetime.now()).days if x else "N/A"
)
user_df["Status Badge"] = user_df.apply(style_status, axis=1)

# 🔍 Search
search_query = st.text_input("🔎 Search users by Name, Email, Hotel, or Country:")
if search_query:
    search_query = search_query.lower()
    filtered_df = user_df[
        user_df.apply(lambda row: 
            search_query in str(row["Name"]).lower() or
            search_query in str(row["Email"]).lower() or
            search_query in str(row["Hotel"]).lower() or
            search_query in str(row["Country"]).lower(), axis=1)
    ]
else:
    filtered_df = user_df

# Show with badge styling
# Show with badge styling
st.markdown("#### 📄 Filtered User List")
for i, row in filtered_df.iterrows():
    cols = st.columns([3, 3, 2, 1, 2])  # Expanded last column for button space

    with cols[0]:
        st.markdown(f"**{row['Name']}**")
        st.caption(f"[{row['Email']}](mailto:{row['Email']})")

    with cols[1]:
        st.markdown(f"🏨 {row['Hotel']} — {row['Country']}")

    with cols[2]:
        st.markdown(f"🕒 Trial Ends In: {row['Trial Ends']} days")

    with cols[3]:
        st.markdown(row["Status Badge"], unsafe_allow_html=True)

    with cols[4]:
        bcol1, bcol2, bcol3 = st.columns([1, 1, 2])

        with bcol1:
            if st.button("🗑️", key=f"delete_{row['ID']}", help="Delete user"):
                c.execute("DELETE FROM users WHERE id = ?", (row["ID"],))
                conn.commit()
                st.success(f"❌ Deleted user {row['Email']}")
                st.rerun()

        with bcol2:
            if row["Status"] == "trial":
                if st.button("⬆️", key=f"upgrade_{row['ID']}", help="Upgrade to Paid"):
                    c.execute("UPDATE users SET subscription_status = 'active' WHERE id = ?", (row["ID"],))
                    conn.commit()
                    st.success(f"✅ Upgraded {row['Email']} to active")
                    st.rerun()

        with bcol3:
            if st.button("🔐", key=f"reset_{row['ID']}", help="Generate Password Reset Token"):
                token = generate_reset_token()
                expiry = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                c.execute("UPDATE users SET reset_token = ?, token_expiry = ? WHERE id = ?", (token, expiry, row["ID"]))
                conn.commit()
                st.info(f"🔑 Token for {row['Email']}: `{token}` (valid 30 mins)")


st.success(f"✅ Displaying {len(filtered_df)} users out of {len(user_df)}")

# 📤 Export CSV + Excel
st.markdown("#### 📁 Export Options")

export_col1, export_col2 = st.columns([2, 9])

with export_col1:
    st.download_button(
        "⬇️ Export as CSV",
        data=filtered_df.drop(columns=["Status Badge"]).to_csv(index=False).encode("utf-8"),
        file_name="ratezap_users.csv",
        mime="text/csv"
    )

with export_col2:
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        filtered_df.drop(columns=["Status Badge"]).to_excel(writer, index=False, sheet_name="Users")
    st.download_button(
        "📊 Export as Excel",
        data=excel_buffer.getvalue(),
        file_name="ratezap_users.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 📧 Email Logs (Placeholder)
st.markdown("#### 📬 Email Logs (Coming Soon...)")
st.info("Email delivery stats will be shown here, e.g. total sent, per user, bounce/failure info.")

# 📊 Company-wise Usage Stats (Optional Future)
st.markdown("#### 🏢 Company-wise Stats (Coming Soon...)")
st.info("You’ll be able to group usage by company/hotel and see submission trends.")

conn.close()
