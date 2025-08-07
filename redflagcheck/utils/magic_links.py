import smtplib
import secrets
from datetime import timedelta
from email.message import EmailMessage
from django.utils import timezone
from redflagcheck.models import User  # Pas indien nodig aan je pad aan
import logging

SMTP_HOST = "smtp.transip.email"
SMTP_PORT = 465
SMTP_USER = "info@redflagcheck.nl"
SMTP_PASSWORD = "=wwvoorRFC137"

def send_magic_link(to_email, token):
    try:
        # Zoek user en genereer unieke magic_code en expiry
        user = User.objects.get(token=token)
        magic_code = secrets.token_urlsafe(24)
        expiry = timezone.now() + timedelta(minutes=30)  # 30 minuten geldig

        user.magic_code = magic_code
        user.magic_code_expiry = expiry
        user.save()

        logging.warning(f"[MAGIC LINK] Nieuw magic_code gezet voor {user.email}: {magic_code} (exp: {expiry})")

        link = f"https://redflagcheck.nl/verifieer/?token={token}&code={magic_code}"
        subject = "Bevestig je e-mailadres"
        body = (
            f"Klik op de onderstaande link om je e-mail te bevestigen:\n\n"
            f"{link}\n\n"
            f"Let op: deze link is persoonlijk en verloopt na 30 minuten."
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg.set_content(body)

        logging.warning(f"📧 Versturen magic link naar: {to_email}")
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.warning(f"✅ Magic link succesvol verzonden naar: {to_email}")
    except Exception as e:
        logging.error(f"❌ Fout bij verzenden e-mail naar {to_email}: {e}")
