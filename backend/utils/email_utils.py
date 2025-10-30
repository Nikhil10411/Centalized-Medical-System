from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
import traceback
import os
import logging

# Load environment variables from the .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Email configuration using environment variables
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),  # Sender's email
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),  # Sender's email password (App Password)
    MAIL_FROM=os.getenv("MAIL_USERNAME"),      # Sender's email (same as username)
    MAIL_PORT=587,                             # Gmail's SMTP port for TLS
    MAIL_SERVER="smtp.gmail.com",              # Gmail's SMTP server
    MAIL_STARTTLS=True,                        # Use StartTLS encryption
    MAIL_SSL_TLS=False,                        # Do not use SSL
    USE_CREDENTIALS=True,                      # Authenticate using credentials
    VALIDATE_CERTS=False                        # Validate SSL/TLS certificates
)

async def send_reset_email(email: str, reset_link: str):
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Password Reset Request</title>
    <style>
      .main {{
        background: #f6f9fc;
        border-radius: 12px;
        color: #1a223f;
        margin: 0 auto;
        padding: 32px 20px 28px 20px;
        width: 100%;
        max-width: 420px;
        font-family: 'Segoe UI', Arial, sans-serif;
        box-shadow: 0 2px 16px rgba(0,0,0,0.10);
      }}
      .btn {{
        background: #00d8ff;
        color: #121626;
        text-decoration: none;
        font-weight: bold;
        border-radius: 6px;
        padding: 12px 26px;
        display: inline-block;
        margin: 16px 0;
        font-size: 16px;
        transition: background 0.2s;
      }}
      .btn:hover {{
        background: #0adbf9;
      }}
      .footer {{
        color: #666;
        margin-top: 32px;
        font-size: 12px;
      }}
    </style>
  </head>
  <body style="background: #f6f9fc; margin: 0; padding: 0;">
    <div class="main">
      <h2 style="color: #00d8ff; margin-top: 0;">Reset Your Password</h2>
      <p>Hello,</p>
      <p>
        We received a request to reset the password for your account.<br>
        To proceed, click the button below:
      </p>
      <p style="text-align: center;">
        <a href="{reset_link}" class="btn">Reset Password</a>
      </p>
      <p>
        If the button does not work, copy and paste this URL in your browser:<br>
        <a href="{reset_link}" style="color:#127bf5;">{reset_link}</a>
      </p>
      <p>
        If you did not request a password reset, please ignore this email—your password will remain unchanged.
      </p>
      <div class="footer">
        &copy; {str(os.getenv("APP_BRAND", "AROVEN"))} {str(os.getenv("APP_YEAR", "2025"))} &mdash; This is an automated message.
      </div>
    </div>
  </body>
</html>
"""
,
        subtype="html",
    )
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        logger.info(f"Email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        traceback.print_exc()  # Print full error trace
        raise Exception("Failed to send reset email")