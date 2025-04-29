
# 📂 File: migrate_night_audit.py
from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3
import os

def migrate_night_audit_table():
    print("🚀 Starting Migration of 'night_audit_history' Table...")

    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Backup original table
        print("🔹 Creating backup table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS night_audit_history_backup AS
            SELECT * FROM night_audit_history
        ''')

        # 2. Rename old table
        print("🔹 Renaming old table...")
        cursor.execute('''
            ALTER TABLE night_audit_history RENAME TO night_audit_history_old
        ''')

        # 3. Create new clean table
        print("🔹 Creating new corrected table...")
        cursor.execute('''
            CREATE TABLE night_audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                audit_date TEXT,
                occupancy_pct INTEGER,
                adr REAL,
                summary_json TEXT,
                extra_fields_json TEXT,
                room_breakdown TEXT,
                hotel_name TEXT,
                created_at TEXT
            )
        ''')

        # 4. Migrate old data into new table
        print("🔹 Migrating data into new table...")
        cursor.execute('''
            INSERT INTO night_audit_history (
                id, user_id, audit_date, occupancy_pct, adr,
                summary_json, extra_fields_json, hotel_name, created_at
            )
            SELECT
                id,
                user_id,
                date,
                occupancy,
                adr,
                summary_data,
                extra_fields,
                hotel_name,
                created_at
            FROM night_audit_history_old
        ''')

        conn.commit()
        conn.close()

        print("✅ Migration completed successfully!")
        print("📦 Backup available as 'night_audit_history_backup'.")
        print("🧹 You can manually delete 'night_audit_history_old' later if all looks good.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_night_audit_table()
