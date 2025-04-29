from utils import hide_streamlit_ui
hide_streamlit_ui()
import smtplib
from email.mime.text import MIMEText

def send_simple_email(to_email, subject, message_body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your_gmail@gmail.com"
    sender_password = "your_password_here"

    msg = MIMEText(message_body, "html")
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
