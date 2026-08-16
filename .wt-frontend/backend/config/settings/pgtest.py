"""B3: PostgreSQL test settings (PostGIS container on localhost:5433)."""
import os
os.environ["CELERY_BROKER_URL"] = "memory://"

from .base import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PG_NAME", "minitender"),
        "USER": os.environ.get("PG_USER", "minitender"),
        "PASSWORD": os.environ.get("PG_PASSWORD", "minitender"),
        "HOST": os.environ.get("PG_HOST", "127.0.0.1"),
        "PORT": os.environ.get("PG_PORT", "5433"),
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
