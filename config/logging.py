LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[ %(asctime)s - %(lineno)d - %(name)s - %(levelname)s - %(message)s ]",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "books": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "common": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
