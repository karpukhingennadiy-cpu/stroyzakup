"""Custom SMTP backend with UTF-8 username support for Cyrillic domains."""
import smtplib, base64
from django.core.mail.backends.smtp import EmailBackend

class UTF8SMTP(smtplib.SMTP):
    """SMTP subclass that supports UTF-8 usernames in AUTH LOGIN."""
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

class UTF8EmailBackend(EmailBackend):
    """Django email backend with UTF-8 username support."""
    def open(self):
        if self.connection:
            return False
        conn = UTF8SMTP(self.host, self.port, timeout=self.timeout)
        conn.starttls(keyfile=self.ssl_keyfile, certfile=self.ssl_certfile)
        conn.login(self.username, self.password)
        self.connection = conn
        return True
