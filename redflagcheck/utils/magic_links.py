import smtplib
from email.message import EmailMessage
import logging

SMTP_HOST = "smtp.transip.email"
SMTP_PORT = 465
SMTP_USER = "info@redflagcheck.nl"
SMTP_PASSWORD = "wwvoorRFC137"

def send_magic_link(to_email, token):
    link = f"https://redflagcheck.nl/verifieer/?token={token}"
    subject = "Bevestig je e-mailadres"
    body = f"Klik op de onderstaande link om je e-mail te bevestigen:\n\n{link}\n\nLet op: deze link is persoonlijk en verloopt na korte tijd."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        logging.warning(f"📧 Versturen magic link naar: {to_email}")
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.warning(f"✅ Magic link succesvol verzonden naar: {to_email}")
    except Exception as e:
        logging.error(f"❌ Fout bij verzenden e-mail naar {to_email}: {e}")
