from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_SERVER=os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT=os.getenv("SMTP_PORT")
SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PASSWORD=os.getenv("SMTP_PASSWORD")


def send_employee_email(subject: str, body: str, recipients: list[str]):
    print("Recipients:", recipients)
    if not recipients:
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
