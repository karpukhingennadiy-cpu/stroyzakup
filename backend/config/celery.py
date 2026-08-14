import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.dev"))
app = Celery("minitender")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.result_backend = getattr(__import__("django.conf", fromlist=["settings"]).settings, "CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
app.conf.result_expires = 3600
app.autodiscover_tasks()

# Global timeouts
app.conf.task_time_limit = 300  # 5 min hard limit
app.conf.task_soft_time_limit = 240  # 4 min soft limit
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
