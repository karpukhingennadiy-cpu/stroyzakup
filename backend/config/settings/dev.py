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


# Inbound email domain for reply addresses

# CORS for frontend dev
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

