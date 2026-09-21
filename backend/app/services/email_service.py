import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def build_otp_email_html(otp: str, user_name: str | None = None, expire_minutes: int = 15) -> str:
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your DermaScan AI Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
    <tr>
      <td align="center" style="padding: 36px 16px;">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 24px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); text-align: center;">
              <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                DermaScan <span style="color: #38bdf8;">AI</span>
              </h1>
              <p style="margin: 6px 0 0; font-size: 13px; color: #94a3b8;">
                Intelligent Skincare & Dermatology Analysis
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding: 32px 32px 24px;">
              <p style="margin: 0 0 16px; font-size: 15px; line-height: 24px; color: #334155;">
                {greeting}
              </p>
              <p style="margin: 0 0 24px; font-size: 14px; line-height: 22px; color: #475569;">
                We received a request to reset the password for your DermaScan AI account. Use the 6-digit verification code below to complete your password reset:
              </p>
              
              <!-- OTP Box -->
              <div style="margin: 28px 0; text-align: center;">
                <div style="display: inline-block; padding: 16px 36px; background-color: #f0fdf4; border: 2px dashed #22c55e; border-radius: 10px;">
                  <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #15803d;">
                    {otp}
                  </span>
                </div>
                <p style="margin: 10px 0 0; font-size: 12px; color: #64748b;">
                  This code expires in <strong>{expire_minutes} minutes</strong>.
                </p>
              </div>

              <p style="margin: 0 0 20px; font-size: 13px; line-height: 20px; color: #64748b;">
                If you did not request this password reset, please ignore this email or reach out to our team if you have concerns. Your password will remain unchanged.
              </p>

              <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 28px 0 20px;">
              <p style="margin: 0; font-size: 11px; color: #94a3b8; text-align: center;">
                &copy; DermaScan AI &bull; Intelligent Skin Analysis Platform
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _send_smtp_email_sync(
    recipient_email: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info(
            "SMTP host not configured. Running in demo mode. OTP dispatched via console."
        )
        return False

    sender_email = settings.smtp_from_email or settings.smtp_user or "no-reply@dermascan-ai.local"
    sender_name = settings.smtp_from_name or "DermaScan AI"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_tls:
                    server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        logger.info("Successfully sent password reset email to %s", recipient_email)
        return True
    except Exception as exc:
        logger.error("Failed to send reset email to %s: %s", recipient_email, exc)
        return False


async def send_password_reset_email(
    recipient_email: str,
    otp: str,
    user_name: str | None = None,
) -> bool:
    settings = get_settings()
    subject = f"{otp} is your DermaScan AI password reset code"
    text_content = (
        f"Your DermaScan AI password reset code is: {otp}\n"
        f"This code will expire in {settings.reset_otp_expire_minutes} minutes.\n"
        f"If you did not request this code, you can safely ignore this email."
    )
    html_content = build_otp_email_html(
        otp=otp,
        user_name=user_name,
        expire_minutes=settings.reset_otp_expire_minutes,
    )

    # Run blocking SMTP calls in threadpool so FastAPI event loop is not blocked
    return await asyncio.to_thread(
        _send_smtp_email_sync,
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
