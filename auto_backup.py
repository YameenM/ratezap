from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3
import os
import shutil
from datetime import datetime

# === CONFIGURATION ===
db_path = "ratezap.db"             # Your main database
backup_folder = "backups"           # Folder to save backups
backup_prefix = "ratezap_backup_"   # Backup file prefix

# === Create backup folder if it doesn't exist ===
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)
    print(f"✅ Created backup folder: {backup_folder}")

# === Create timestamped backup filename ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_filename = f"{backup_prefix}{timestamp}.db"
backup_path = os.path.join(backup_folder, backup_filename)

# === Copy database ===
try:
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup successful! Saved to {backup_path}")
except Exception as e:
    print(f"❌ Backup failed: {e}")
