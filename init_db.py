import sqlite3
import hashlib
from utils import hide_streamlit_ui
hide_streamlit_ui()
# Database path
db_path = "ratezap.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# USERS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    subscription_status TEXT,
    trial_start TEXT,
    hotel_name TEXT,
    city TEXT,
    country TEXT,
    phone TEXT,
    reset_token TEXT,
    token_expiry TEXT
)
''')

# USER SETTINGS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    prop_type TEXT,
    prop_name TEXT,
    city TEXT,
    country TEXT,
    currency TEXT
)
''')

# RATE HISTORY TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS rate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    occupancy INTEGER,
    competitor_rate REAL,
    local_event TEXT,
    day_type TEXT,
    currency TEXT,
    suggested_rate REAL,
    hotel_type TEXT,
    hotel_name TEXT,
    user_id INTEGER
)
''')

# NIGHT AUDIT HISTORY TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS night_audit_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    occupancy INTEGER,
    adr REAL,
    summary_data TEXT,
    extra_fields TEXT,
    room_breakdown TEXT,
    hotel_name TEXT,
    created_at TEXT
)
''')

# ANNUAL RATES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS annual_rates (
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
)
''')



# COMPANIES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    company_name TEXT UNIQUE,
    company_code TEXT UNIQUE,
    created_at TEXT
)

''')


# Ensure admin user exists

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

admin_email = "admin@ratezap.com"
admin_password = hash_password("admin123")
c.execute("SELECT * FROM users WHERE email = ?", (admin_email,))
if not c.fetchone():
    c.execute('''
        INSERT INTO users (full_name, email, password, subscription_status, trial_start, hotel_name, city, country, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Admin", admin_email, admin_password, "pro", "2025-01-01", "RateZap HQ", "Austin", "USA", "0000000000"))
    print("✅ Admin user created.")
else:
    print("⚠️ Admin user already exists.")

conn.commit()
conn.close()
print("✅ All tables created successfully!")
