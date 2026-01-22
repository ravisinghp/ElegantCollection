# from email.policy import SMTP
# import smtplib
# from email.mime.text import MIMEText

from email.mime.text import MIMEText
import smtplib


SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_EMAIL="icapture.notify@gmail.com"      # your gmail
SMTP_PASSWORD="anhv qjee jcyh gouf"      # gmail app password

# EMPLOYEE_EMAILS = [
#     "mansi.dedhia@planfirma.com",
#     # "employee2@company.com",
# ]

# def send_employee_email(subject: str, body: str):
#     msg = MIMEText(body)
#     msg["Subject"] = "Missing/Mismatch"
#     msg["From"] = SMTP_EMAIL
#     msg["To"] = ", ".join(EMPLOYEE_EMAILS)

#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_EMAIL, SMTP_PASSWORD)
#         server.send_message(msg)


# for dynamic 


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
