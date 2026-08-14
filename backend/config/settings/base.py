import os
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Export .env secrets to os.environ for service modules that read env directly
# (decouple.config() does NOT populate os.environ by itself)
for _env_key in ("LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL",
                 "DADATA_TOKEN", "YANDEX_GEOCODER_KEY", "GEOCODER_API_KEY", "FROM_EMAIL"):
    os.environ.setdefault(_env_key, config(_env_key, default=""))

SECRET_KEY="dev-secret-key"
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "apps.accounts",
    "apps.requests",
    "apps.suppliers",
    "apps.quotes",
    "apps.emails",
    "apps.admin_ext",
    "apps.analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config("DB_NAME", default="minitender"),
        "USER": config("DB_USER", default="minitender"),
        "PASSWORD": "minitender",
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
# B2: when True, parse/match/send_rfq run as Celery tasks and views return 202+task_id.
# When False (dev default), everything stays synchronous.
USE_CELERY = config("USE_CELERY", default=False, cast=bool)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# LLM (DeepSeek API)
LLM_API_KEY = config("LLM_API_KEY", default="")
LLM_MODEL = config("LLM_MODEL", default="deepseek-chat")
LLM_BASE_URL = config("LLM_BASE_URL", default="https://api.deepseek.com/v1")

# Email (configured via .env, defaults for dev)
EMAIL_BACKEND = config("EMAIL_BACKEND", default="apps.emails.utf8_smtp.UTF8EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.beget.com")
EMAIL_PORT = config("EMAIL_PORT", default=465, cast=int)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="rfq@минитендер.рф")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Минитендер RFQ <rfq@xn--d1abbjawic3ap.xn--p1ai>")
INBOUND_EMAIL_DOMAIN = config("INBOUND_EMAIL_DOMAIN", default="in.xn--d1abbjawic3ap.xn--p1ai")

# B1: IMAP polling for supplier replies
INBOUND_IMAP_HOST = config("INBOUND_IMAP_HOST", default="")
INBOUND_IMAP_PORT = config("INBOUND_IMAP_PORT", default=993, cast=int)
INBOUND_IMAP_USER = config("INBOUND_IMAP_USER", default="")
INBOUND_IMAP_PASSWORD = config("INBOUND_IMAP_PASSWORD", default="")
INBOUND_IMAP_FOLDER = config("INBOUND_IMAP_FOLDER", default="INBOX")

# Whitenoise
STORAGES={"staticfiles":{"BACKEND":"whitenoise.storage.CompressedManifestStaticFilesStorage"}}
# Frontend URL
FRONTEND_URL=config("FRONTEND_URL",default="http://localhost:3000")
