# This will make sure the Celery app is loaded when Django starts
from config.celery import app as celery_app

__all__ = ("celery_app",)
