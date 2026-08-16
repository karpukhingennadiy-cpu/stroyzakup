"""Custom SMTP backend with UTF-8 username support for Cyrillic domains."""
import smtplib, base64
from django.core.mail.backends.smtp import EmailBackend


class UTF8SMTPLoginMixin:
    """AUTH LOGIN with UTF-8 base64-encoded username (Cyrillic mailbox names)."""
    def login(self, user, password, *, initial_response_ok=True):
        self.ehlo('minitender')
        self.docmd('AUTH', 'LOGIN')
        user_b64 = base64.b64encode(user.encode('utf-8')).decode()
        self.docmd(user_b64)
        pw_b64 = base64.b64encode(password.encode('utf-8')).decode()
        code, resp = self.docmd(pw_b64)
        if code != 235:
            raise smtplib.SMTPAuthenticationError(code, resp)
        return (code, resp)


class UTF8SMTP(UTF8SMTPLoginMixin, smtplib.SMTP):
    """Plain SMTP + STARTTLS with UTF-8 username support."""


class UTF8SMTP_SSL(UTF8SMTPLoginMixin, smtplib.SMTP_SSL):
    """SMTPS (SSL from connect, port 465) with UTF-8 username support."""


class UTF8EmailBackend(EmailBackend):
    """Django email backend with UTF-8 username support.
    Honors EMAIL_USE_SSL (SMTPS) and EMAIL_USE_TLS (STARTTLS)."""
    def open(self):
        if self.connection:
            return False
        try:
            if self.use_ssl:
                conn = UTF8SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                conn = UTF8SMTP(self.host, self.port, timeout=self.timeout)
                if self.use_tls:
                    conn.starttls()
            if self.username and self.password:
                conn.login(self.username, self.password)
            self.connection = conn
            return True
        except OSError:
            if not self.fail_silently:
                raise
            return False
