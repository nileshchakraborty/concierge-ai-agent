import os
from email.message import EmailMessage
from typing import Optional

try:
    import aiosmtplib
except Exception:
    aiosmtplib = None

SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")


async def send_email(to_address: str, subject: str, body: str, client: Optional[object] = None) -> dict:
    """Asynchronously send email using aiosmtplib if available.

    Returns a dict with success status and message or error.
    """
    if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD or not SENDER_EMAIL:
        return {"success": False, "error": "SMTP configuration incomplete"}

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    from_addr = SENDER_EMAIL or SMTP_USERNAME
    msg["From"] = from_addr
    msg["To"] = to_address

    if aiosmtplib is None:
        return {"success": False, "error": "aiosmtplib not installed"}

    try:
        smtp = aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=(SMTP_PORT == 465))
        await smtp.connect()
        if SMTP_PORT != 465:
            await smtp.starttls()
        await smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        await smtp.send_message(msg)
        await smtp.quit()
        return {"success": True, "message": f"Email sent to {to_address}"}
    except aiosmtplib.errors.SMTPAuthenticationError:
        return {"success": False, "error": "SMTP authentication failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}
