import os
from pathlib import Path
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
for env_path in (BASE_DIR.parent / ".env", BASE_DIR / ".env"):
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = val
            break
        except Exception:
            pass


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-skillsphere-dev-key-change-in-production",
)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False").strip().lower() in ("true", "1", "yes")

allowed_hosts_str = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(",") if h.strip()] if allowed_hosts_str else []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "corsheaders",

    # Project apps
    "accounts",
    "courses",
    "enrollments",
    "learning",
    "quizzes",
    "certificates",
    "reviews",
    "notifications",
    "ai_assistant",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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


# Database
# PostgreSQL

DB_NAME = os.environ.get(
    "DB_NAME",
    os.environ.get("POSTGRES_DB", "skillsphere")
)
DB_USER = os.environ.get(
    "DB_USER",
    os.environ.get("POSTGRES_USER", "skillsphere_user")
)
DB_PASSWORD = os.environ.get(
    "DB_PASSWORD",
    os.environ.get("POSTGRES_PASSWORD", "skillsphere_password")
)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5436")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# Password validation

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


# Custom user model

AUTH_USER_MODEL = "accounts.User"


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files

STATIC_URL = "static/"


# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework

AI_RATE_LIMIT = os.environ.get("AI_RATE_LIMIT", "30/minute").strip()

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "ai_assistant": AI_RATE_LIMIT,
        "anon": os.environ.get("ANON_THROTTLE_RATE", "100/minute"),
        "user": os.environ.get("USER_THROTTLE_RATE", "1000/minute"),
    },
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
}


# Logging Configuration (Stage 16)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "skillsphere": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "config.exceptions": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


# JWT Configuration

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}


# CORS Configuration
# Allow the Angular development server to access Django APIs.

cors_origins_str = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200"
)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in cors_origins_str.split(",")
    if origin.strip()
]


# ============================================================
# AI LEARNING ASSISTANT CONFIGURATION (Stage 14 & 15)
# ============================================================

AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").strip().lower()
AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
AI_MODEL = os.environ.get("AI_MODEL", "gemini-1.5-flash").strip()
AI_REQUEST_TIMEOUT = int(os.environ.get("AI_REQUEST_TIMEOUT", "30").strip() or 30)

# Stage 15 Context & Safety Limits
AI_MAX_LESSON_CHARS = int(os.environ.get("AI_MAX_LESSON_CHARS", "15000").strip() or 15000)
AI_MAX_MESSAGE_CHARS = int(os.environ.get("AI_MAX_MESSAGE_CHARS", "2000").strip() or 2000)
AI_MAX_RESPONSE_CHARS = int(os.environ.get("AI_MAX_RESPONSE_CHARS", "4000").strip() or 4000)

 