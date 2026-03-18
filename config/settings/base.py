# BookShelf 2 Base Settings
import os
import environ
from pathlib import Path
from datetime import timedelta
from config.logging import LOGGING
from common.constants import (
    THROTTLE_RATE_ANON,
    THROTTLE_RATE_USER,
    THROTTLE_RATE_IP,
    THROTTLE_RATE_AUTH,
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    SECRET_KEY=(str, ""),
    JWT_ACCESS_TOKEN_MINUTES=(int, 60),
    JWT_REFRESH_TOKEN_DAYS=(int, 1),
    OTP_EXPIRY_MINUTES=(int, 15),
    USER_DATA_RETENTION_DAYS=(int, 30),
    UNVERIFIED_USER_CLEANUP_HOURS=(int, 24),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")

# Business Configuration (from .env)
OTP_EXPIRY_MINUTES = env("OTP_EXPIRY_MINUTES")
USER_DATA_RETENTION_DAYS = env("USER_DATA_RETENTION_DAYS")
UNVERIFIED_USER_CLEANUP_HOURS = env("UNVERIFIED_USER_CLEANUP_HOURS")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework",
    "django_filters",
    "accounts",
    "books",
    "common",
    "tenants",
    "payments",
    "silk",
    "debug_toolbar",
]

MIDDLEWARE = [
    "common.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "tenants.middleware.TenantMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.RequestLogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.API404Middleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

AUTH_USER_MODEL = "accounts.User"

# Authentication backends for login
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "tenants.authentication.TenantAwareJWTAuthentication",
    ],
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": (
            "10000/minute"
            if env.bool("LOCUST_PERF_TEST", default=False)
            else THROTTLE_RATE_ANON
        ),
        "user": (
            "10000/minute"
            if env.bool("LOCUST_PERF_TEST", default=False)
            else THROTTLE_RATE_USER
        ),
        "ip_throttle": (
            "10000/minute"
            if env.bool("LOCUST_PERF_TEST", default=False)
            else THROTTLE_RATE_IP
        ),
        "auth_throttle": (
            "10000/minute"
            if env.bool("LOCUST_PERF_TEST", default=False)
            else THROTTLE_RATE_AUTH
        ),
    },
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False if env.bool("LOCUST_PERF_TEST", default=False) else True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SITE_URL = env("SITE_URL", default="http://127.0.0.1:8000")


# Razorpay Settings
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET", default="")
PREMIUM_PRICE_PAISE = 99900  # ₹999
USER_DATA_RETENTION_DAYS = env.int("USER_DATA_RETENTION_DAYS", default=30)
TENANT_DATA_RETENTION_DAYS = env.int("TENANT_DATA_RETENTION_DAYS", default=360)

INTERNAL_IPS = [
    "127.0.0.1",
    "::1",
]


def show_toolbar(request):
    """Custom function to hide toolbar on specific paths like /silk/"""
    if not request.path or any(
        request.path.startswith(p) for p in ["/silk/", "/health/"]
    ):
        return False
    from django.conf import settings

    return settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS


# Debug Toolbar Configuration (Hide Silk noise)
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "config.settings.base.show_toolbar",
    "HIDE_IN_STACKTRACES": (
        "silk",
        "django.db.backends",
        "django.core.handlers",
        "django.core.servers",
        "django.utils.decorators",
        "django.utils.deprecation",
        "django.utils.functional",
    ),
    "SHOW_COLLAPSED": True,
    "IGNORE_SQL_PATTERNS": (
        r"silk_",
        r"SAVEPOINT",
        r"RELEASE SAVEPOINT",
    ),
}

# Silence Silk for Admin/Debug pages (using regex patterns)
SILKY_IGNORE_PATHS = [
    r"^/admin/",
    r"^/silk/",
    r"^/__debug__/",
    r"^/health/",
]
