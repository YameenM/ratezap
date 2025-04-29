
# config.py
import os
import streamlit as st

try:
    # 👉 Try loading from Streamlit Cloud secrets
    EMAIL_ADDRESS = st.secrets["email"]["address"]
    EMAIL_PASSWORD = st.secrets["email"]["password"]
    SMTP_SERVER = st.secrets["email"]["smtp"]
    SMTP_PORT = int(st.secrets["email"]["port"])
except Exception:
    # 👉 Fallback to local .env (for local dev)
    from dotenv import load_dotenv
    load_dotenv()
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
