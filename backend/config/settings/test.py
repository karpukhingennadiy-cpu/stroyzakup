"""Test settings for CI/CD."""
import os
os.environ["CELERY_BROKER_URL"] = "memory://"

from .base import *

# FIX-CI: remove django.contrib.gis — no GDAL in CI
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
