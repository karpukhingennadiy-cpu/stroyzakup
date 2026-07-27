from .base import *

DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "localhost", "127.0.0.1"]

# SQLite for local dev (no Docker needed)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST="smtp.mail.ru"
EMAIL_PORT=465
EMAIL_USE_SSL=True

# Inbound email domain for reply addresses
INBOUND_EMAIL_DOMAIN = "in.minitender.ru"
INBOUND_EMAIL_WEBHOOK_SECRET = "dev-webhook-secret"

# CORS for frontend dev
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

EMAIL_HOST_USER="309651@mail.ru"
EMAIL_HOST_PASSWORD="uePMzMa4IhccRLwSUh1R"
