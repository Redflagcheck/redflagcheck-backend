import os
import logging
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# --- Load .env only for local/dev ---
load_dotenv()

# --- Logging (console) ---
logging.basicConfig(level=logging.INFO)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security & Debug via env ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")  # In Render als env var zetten

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# --- Hosts & Proxy headers ---
def _split_env(name: str, default: str = ""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]

ALLOWED_HOSTS = [
    "redflagcheck-new.onrender.com",
    "redflagcheck.nl",
    "www.redflagcheck.nl",
    "127.0.0.1",
    "localhost",
    'redflagcheck-new.onrender.com',
]


logging.info(f"ALLOWED_HOSTS at boot: {ALLOWED_HOSTS}")



USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"

# --- Optional: API key uit env (niet hardcoderen) ---
RFC_API_KEY = os.getenv("RFC_API_KEY", "")

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "corsheaders",
    "rest_framework",
    "django_extensions",
    # local apps
    "redflagcheck",
]

# --- Middleware (volgorde belangrijk) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # vóór CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

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

WSGI_APPLICATION = "backend.wsgi.application"

# --- Database via DATABASE_URL (Render) met veilige defaults ---
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", ""), conn_max_age=600, ssl_require=True
    )
}

# --- Password validators ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / TZ ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# --- Static (Whitenoise) ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Media (optioneel; Render static only — voor media gebruik S3/Cloud storage) ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- CORS/CSRF helpers ---
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = _split_env(
    "CORS_ALLOWED_ORIGINS",
    "https://redflagcheck.nl,https://www.redflagcheck.nl,https://redflagcheck-backend-y06m.onrender.com",
)
CORS_ALLOW_CREDENTIALS = False  # zet alleen True als je cookies/credentials nodig hebt

CSRF_TRUSTED_ORIGINS = _split_env(
    "CSRF_TRUSTED_ORIGINS",
    "https://redflagcheck.nl,https://www.redflagcheck.nl,https://redflagcheck-backend-y06m.onrender.com",
)

# --- DRF (optioneel basis) ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

# --- Logging wat netter op console ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            "datefmt": "%H:%M:%S"
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard", "level": "INFO"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "redflagcheck": {"level": "INFO", "handlers": ["console"], "propagate": True},
        "django": {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
}

# --- Default PK ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
