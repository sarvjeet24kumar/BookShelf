from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context_filter": {
            "()": "common.logging_utils.LogContextFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": (
                "[ %(asctime)s - %(lineno)d - %(name)s - %(levelname)s "
                "- request_id=%(request_id)s tenant_id=%(tenant_id)s "
                "- %(message)s ]"
            ),
        },
        "simple": {
            "format": (
                "[ %(asctime)s - %(lineno)d - %(name)s - %(levelname)s "
                "- %(message)s ]"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["context_filter"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["context_filter"],
            "level": "INFO",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["context_filter"],
            "level": "ERROR",
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "level": "INFO",
            "propagate": True,
        },
        "accounts": {
            "level": "DEBUG",
            "propagate": True,
        },
        "books": {
            "level": "DEBUG",
            "propagate": True,
        },
        "common": {
            "level": "DEBUG",
            "propagate": True,
        },
        "payments": {
            "level": "DEBUG",
            "propagate": True,
        },
        "tenants": {
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
