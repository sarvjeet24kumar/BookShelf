import os
from celery import Celery
from celery.schedules import timedelta, crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("bookshelf")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


app.conf.beat_schedule = {
    "cleanup-unverified-users": {
        "task": "accounts.tasks.cleanup_unverified_users",
        "schedule": timedelta(hours=24),
    },
    "cleanup-deleted-users-data": {
        "task": "accounts.tasks.cleanup_deleted_users_data",
        "schedule": timedelta(hours=24),
    },
    "reconcile-payments": {
        "task": "payments.tasks.reconcile_payments_task",
        "schedule": crontab(minute="*/15"),
    },
}
