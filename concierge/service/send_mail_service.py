from ..client.send_mail_client import SendMailClient

class SendMailService:

    _send_mail_client: SendMailClient

    def send_mail(self, to_address: str, subject: str, body: str) -> bool:
        # Implementation of sending email using SMTP server
        self._send_mail_client.send_email(to_address, subject, body)
        return True