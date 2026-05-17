import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send(self, recipient: str, subject: str, body: str) -> bool:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email_from or settings.smtp_user
        message["To"] = recipient
        message.set_content(body)

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
            ) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
        except Exception as exc:
            logger.error(
                "[EmailService] Slanje e-maila nije uspjelo. "
                "Primatelj: %s, Naslov: %s, Greška: %s",
                recipient,
                subject,
                exc,
            )
            return False

        logger.info(
            "[EmailService] E-mail uspješno poslan. Primatelj: %s, Naslov: %s",
            recipient,
            subject,
        )
        return True
