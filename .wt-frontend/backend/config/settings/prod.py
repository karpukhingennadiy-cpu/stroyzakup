from .base import *

DEBUG = False

SECRET_KEY = config("SECRET_KEY")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="минитендер.рф,app.минитендер.рф,localhost,127.0.0.1", cast=Csv())

# Геоданные хранятся в Float-полях — django.contrib.gis и GDAL не нужны
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]

# Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "SAMEORIGIN"

# CSRF & CORS
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="https://минитендер.рф,https://app.минитендер.рф", cast=Csv())
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="https://минитендер.рф,https://app.минитендер.рф", cast=Csv())

# Email — use real SMTP in production
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.beget.com")
EMAIL_PORT = config("EMAIL_PORT", default=465, cast=int)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Минитендер RFQ <rfq@xn--d1abbjawic3ap.xn--p1ai>")
INBOUND_EMAIL_DOMAIN = config("INBOUND_EMAIL_DOMAIN", default="in.xn--d1abbjawic3ap.xn--p1ai")

# Database — PostgreSQL in production (без PostGIS: координаты — FloatField)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="minitender"),
        "USER": config("DB_USER", default="minitender"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")

# Static
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
