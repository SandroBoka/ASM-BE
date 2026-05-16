import logging

logger = logging.getLogger(__name__)


class EmailService:
    def send(self, recipient: str, subject: str, body: str) -> bool:
        logger.info(
            "[EmailService MOCK] Slanje e-maila\n"
            "  Primatelj: %s\n"
            "  Naslov:    %s\n"
            "  Tijelo:\n%s",
            recipient,
            subject,
            body,
        )
        return True
