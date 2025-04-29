from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3

# Path to your database
db_path = "ratezap.db"

# Define required tables and columns
required_schema = {
    "users": ["id", "full_name", "email", "password", "subscription_status", "trial_start", "hotel_name", "city", "country", "phone", "reset_token", "token_expiry"],
    "user_settings": ["user_id", "prop_type", "prop_name", "city", "country", "currency"],
    "rate_history": ["id", "timestamp", "occupancy", "competitor_rate", "local_event", "day_type", "currency", "suggested_rate", "hotel_type", "hotel_name", "user_id"],
    "night_audit_history": ["id", "user_id", "date", "occupancy", "adr", "summary_data", "extra_fields", "room_breakdown", "hotel_name", "created_at"],
    "annual_rates": ["id", "user_id", "company_code", "company_name", "from_date", "to_date", "room_type", "meal_plan", "daily_rate", "weekend_rate", "holiday_rate", "notes", "created_at"],
    "companies": ["id", "user_id", "company_name", "company_code", "created_at"]
}

def check_table_and_columns(conn, table, expected_columns):
    try:
        c = conn.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in c.fetchall()]
        
        missing = []
        for col in expected_columns:
            if col not in existing_columns:
                missing.append(col)

        if not missing:
            print(f"✅ Table `{table}`: All required columns exist.")
        else:
            print(f"❌ Table `{table}`: Missing columns -> {', '.join(missing)}")

    except Exception as e:
        print(f"❌ Error checking table `{table}`: {e}")

def main():
    print("🔍 Starting Database Health Check...\n")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for table, columns in required_schema.items():
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if c.fetchone():
            check_table_and_columns(conn, table, columns)
        else:
            print(f"❌ Table `{table}` does not exist!")

    conn.close()
    print("\n🏁 Health Check Completed.")

if __name__ == "__main__":
    main()
