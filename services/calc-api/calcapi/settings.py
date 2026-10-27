import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("CALC_DEBUG", "1") == "1"

secret_key = os.environ.get("CALC_SECRET_KEY")
allowed_hosts_value = os.environ.get("CALC_ALLOWED_HOSTS")

if DEBUG:
    SECRET_KEY = secret_key or "dev-only-not-for-production"
    ALLOWED_HOSTS = [
        host.strip()
        for host in (allowed_hosts_value or "*").split(",")
        if host.strip()
    ]
else:
    if not secret_key:
        raise ImproperlyConfigured(
            "CALC_SECRET_KEY must be set when CALC_DEBUG is not 1"
        )
    ALLOWED_HOSTS = [
        host.strip()
        for host in (allowed_hosts_value or "").split(",")
        if host.strip()
    ]
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "CALC_ALLOWED_HOSTS must list at least one host when CALC_DEBUG is not 1"
        )
    SECRET_KEY = secret_key

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "calc_runs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "calcapi.middleware.DevCorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "calcapi.urls"
WSGI_APPLICATION = "calcapi.wsgi.application"

if os.environ.get("CALC_DB_ENGINE", "").lower() == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("CALC_DB_NAME", ""),
            "USER": os.environ.get("CALC_DB_USER", ""),
            "PASSWORD": os.environ.get("CALC_DB_PASSWORD", ""),
            "HOST": os.environ.get("CALC_DB_HOST", ""),
            "PORT": os.environ.get("CALC_DB_PORT", ""),
            "CONN_MAX_AGE": int(os.environ.get("CALC_DB_CONN_MAX_AGE", "0") or 0),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("CALC_DB_NAME") or BASE_DIR / "db.sqlite3",
        }
    }

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.SessionAuthentication401",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

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

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [
    value
    for value in os.environ.get("CALC_CSRF_TRUSTED_ORIGINS", "").split(",")
    if value
]
