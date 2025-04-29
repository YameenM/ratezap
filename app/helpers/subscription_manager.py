
from utils import hide_streamlit_ui
hide_streamlit_ui()
import sqlite3
from datetime import datetime, timedelta

def check_trial_expiry(user_id):
    conn = sqlite3.connect("ratezap.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("SELECT trial_start, subscription_status FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()

    if row:
        trial_start, status = row
        if status == "trial" and trial_start:
            trial_date = datetime.strptime(trial_start, "%Y-%m-%d")
            if datetime.now() > trial_date + timedelta(days=7):
                # Expire trial
                c.execute("UPDATE users SET subscription_status = 'expired' WHERE id = ?", (user_id,))
                conn.commit()
                return "expired"
    return "active"
