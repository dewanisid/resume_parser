import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("resume_parser")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "apps.parser.tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
}
