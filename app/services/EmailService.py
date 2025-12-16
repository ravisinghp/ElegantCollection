from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.models.schemas.AdminSchema import EmailSettings


class EmailService:
    def __init__(self) -> None:
        self.settings = EmailSettings()
        self.conf = ConnectionConfig(
            MAIL_USERNAME=self.settings.MAIL_USERNAME,
            MAIL_PASSWORD=self.settings.MAIL_PASSWORD,
            MAIL_FROM=self.settings.MAIL_FROM,
            MAIL_FROM_NAME=self.settings.MAIL_FROM_NAME,
            MAIL_PORT=self.settings.MAIL_PORT,
            MAIL_SERVER=self.settings.MAIL_SERVER,
            MAIL_STARTTLS=self.settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=self.settings.USE_CREDENTIALS,
        )
        self.mailer = FastMail(self.conf)

    async def send_email(
        self,
        subject: str,
        recipients: List[str],
        body: str,
        subtype: str = "plain",
    ) -> None:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=subtype,
        )
        await self.mailer.send_message(message)
        print("Email sent successfully!")

    async def send_welcome_email(
        self,
        user_name: str,
        email: str,
        password: Optional[str] = None,
        login_link: str=None
    ) -> None:
        body_lines = [
            f"Hello {user_name},",
            "",
            "Your account has been created successfully!",
            
            f"You can login using the following link:{login_link}"
        ]
        if password:
            body_lines.extend([
                "",
                "Login details:",
                f"Email: {email}",
                f"Password: {password}",
            ])
        body_lines.extend([
            "",
            "Regards,",
            "Support Team",
        ])
        body = "\n".join(body_lines)
        try:
            await self.send_email(
                subject="Welcome to Our Platform",
                recipients=[email],
                body=body,
                subtype="plain",
            )
        except Exception as e:
            # Swallow errors by default; callers can choose to handle differently
            print(f"Failed to send welcome email: {e}")
            pass

    
    async def send_forgot_password_email(
        self,
        user_name: str,
        email: str,
        reset_link: str, 
        password: Optional[str] = None,
        
    ) -> None:
        body_lines = [
            f"Hello {user_name},",
             "You requested to reset your password.",
             f"Please click the link below to reset your password:",
              f"{reset_link}",  # include the reset link here
        ]
        if password:
            body_lines.extend([
                "",
                "Login details:",
                f"Email: {email}",
                f"Password: {password}",
            ])
        body_lines.extend([
            "",
            "Regards,",
            "Support Team",
        ])
        body = "\n".join(body_lines)
        try:
            await self.send_email(
                subject="Reset Password Confirmation",
                recipients=[email],
                body=body,
                subtype="plain",
            )
        except Exception as e:
          print(f"Failed to send reset password email: {e}")
          raise e  # <-- ensures the caller knows



    async def send_password_changed_email(self, user_name: str, email: str,login_link: str=None):
        body_lines = [
                    f"Hello {user_name},",
                "",
                "Your password has been changed successfully.",
                "",
                f"You can login using the following link: {login_link}",  #space added
                "",
                "Regards,",
                "Support Team",
        ]
        body = "\n".join(body_lines)

        await self.send_email(
            subject="Your Password Has Been Changed",
            recipients=[email],
            body=body,
            subtype="plain"
        )
