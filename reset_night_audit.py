
# 📂 File: reset_night_audit.py
from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3
import os
import shutil
from datetime import datetime

def reset_night_audit_history():
    print("🛡 Safe DB Reset Started...")

    db_path = "/mnt/data/ratezap.db" if os.path.exists("/mnt/data") else "ratezap.db"

    # Step 1: Backup whole DB file (optional but smart)
    backup_path = f"{db_path.replace('.db', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy(db_path, backup_path)
        print(f"✅ Database file backed up at: {backup_path}")
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")

    # Step 2: Connect and reset only night_audit_history table
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🧹 Deleting all records from night_audit_history...")
        cursor.execute("DELETE FROM night_audit_history;")
        conn.commit()
        conn.close()

        print("✅ All night audit records deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to reset night audits: {e}")

if __name__ == "__main__":
    reset_night_audit_history()
