import os
import logging
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Alleen lokale .env laden
load_dotenv()

# --- Paden ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Helpers ---
def _split_env(name: str, default: str = ""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]

# --- Security / Debug ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Render geeft dit mee; gebruiken als default host
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()

_default_allowed = "127.0.0.1,localhost"
if RENDER_HOST:
    # jouw concrete service + alle onrender-subdomeinen als fallback
    _default_allowed = f"{RENDER_HOST},.onrender.com," + _default_allowed

ALLOWED_HOSTS = _split_env("ALLOWED_HOSTS", _default_allowed)

# Achter Render/Cloudflare zit je achter een proxy:
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"

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
    # local
    "redflagcheck",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

# --- Database (Render Postgres via DATABASE_URL) ---
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", ""),
        conn_max_age=600,
        ssl_require=True,
    )
}

# --- Password validators ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]