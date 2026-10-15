import os
import sys
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, unquote, parse_qs
from django.core.exceptions import ImproperlyConfigured


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
INSECURE_DEV_SECRET_KEY = "django-insecure-skillsphere-dev-key-change-in-production"
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    INSECURE_DEV_SECRET_KEY,
).strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False").strip().lower() in ("true", "1", "yes")

# In local development mode, if SECRET_KEY is empty, fallback to dev secret
if DEBUG and not SECRET_KEY:
    SECRET_KEY = INSECURE_DEV_SECRET_KEY


def validate_production_secret(secret_key: str, debug: bool) -> None:
    """
    Validate that production deployments (DEBUG=False) have a valid, secure SECRET_KEY.
    Raises ImproperlyConfigured if the secret is missing, empty, or set to the known
    insecure development default. Never prints or reveals the secret value in errors.
    """
    if not debug:
        if not secret_key or secret_key == INSECURE_DEV_SECRET_KEY:
            raise ImproperlyConfigured(
                "Production security validation failed: SECRET_KEY is missing, empty, "
                "or set to the known development fallback. "
                "Set a unique, cryptographically strong SECRET_KEY environment variable "
                "when DEBUG is False."
            )


# Perform startup validation for production mode (unless running in test runner or static collection)
if not any(arg in sys.argv for arg in ("test", "collectstatic")):
    validate_production_secret(SECRET_KEY, DEBUG)

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

# Database Connection Lifetime (CONN_MAX_AGE)
# In local development, 0 closes connections after each request, avoiding idle connections.
# In production with persistent Gunicorn workers, setting a positive integer (e.g. 60-600s)
# allows connection reuse, reducing connection establishment overhead with PostgreSQL.
def parse_conn_max_age(value: str | None, default: int = 0) -> int:
    """
    Parse database connection lifetime in seconds.
    Normalizes negative values to 0 and safely falls back to default on invalid or empty input.
    """
    if value is None:
        return default
    try:
        return max(0, int(str(value).strip()))
    except (ValueError, TypeError):
        return default


CONN_MAX_AGE = parse_conn_max_age(os.environ.get("CONN_MAX_AGE", "0"))


def parse_database_url(url: str) -> dict:
    """
    Parse a postgresql:// or postgres:// connection URL into Django DATABASES config parameters.
    Safely decodes percent-encoded usernames and passwords using standard library urllib.parse.
    Extracts query parameters (such as sslmode) into the OPTIONS dictionary.
    Never logs or exposes credentials.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise ValueError("Unsupported database scheme in DATABASE_URL. Must begin with postgresql:// or postgres://.")

    if not parsed.hostname:
        raise ValueError("DATABASE_URL must include a valid hostname.")

    try:
        raw_port = parsed.port
    except ValueError:
        raise ValueError("DATABASE_URL contains an invalid port.") from None

    if raw_port is not None and not (1 <= raw_port <= 65535):
        raise ValueError("DATABASE_URL contains an invalid port.")

    name = parsed.path.lstrip("/") or "postgres"
    user = unquote(parsed.username) if parsed.username else ""
    password = unquote(parsed.password) if parsed.password else ""
    host = parsed.hostname
    port = str(raw_port) if raw_port is not None else "5432"

    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
    }

    query_params = parse_qs(parsed.query)
    options = {}
    if "sslmode" in query_params and query_params["sslmode"]:
        options["sslmode"] = query_params["sslmode"][0]

    if options:
        config["OPTIONS"] = options

    return config


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_SSLMODE = os.environ.get("DB_SSLMODE", "").strip()

if DATABASE_URL:
    default_db_config = parse_database_url(DATABASE_URL)
    default_db_config["CONN_MAX_AGE"] = CONN_MAX_AGE
    if DB_SSLMODE:
        default_db_config.setdefault("OPTIONS", {})["sslmode"] = DB_SSLMODE
    DATABASES = {
        "default": default_db_config
    }
else:
    default_db_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "CONN_MAX_AGE": CONN_MAX_AGE,
    }
    if DB_SSLMODE:
        default_db_config["OPTIONS"] = {"sslmode": DB_SSLMODE}
    DATABASES = {
        "default": default_db_config
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

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


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


# CSRF Trusted Origins (Stage 22.2)
# In Django 4.0+ / 6.1+, POST requests sent over HTTPS or from separate origins
# require the origin to be listed in CSRF_TRUSTED_ORIGINS.
# Wildcards ('*') are unsafe and strictly disallowed.
# In local development (DEBUG=True) or local Docker testing where ALLOWED_HOSTS
# includes localhost / 127.0.0.1, localhost origins are trusted by default.
# In production (DEBUG=False without localhost in ALLOWED_HOSTS), defaults to empty
# so that production deployments must explicitly declare trusted HTTPS origins.
DEFAULT_LOCAL_CSRF_ORIGINS = (
    "http://localhost:4200,http://127.0.0.1:4200,http://localhost:8000,http://127.0.0.1:8000"
)


def get_default_csrf_trusted_origins(debug: bool, allowed_hosts: list[str]) -> str:
    """
    Determine default CSRF trusted origins string based on environment.
    Retains localhost origins for local development (debug=True) and local Docker (localhost in allowed_hosts).
    Defaults to empty string for production deployments with public hostnames.
    """
    if debug or "localhost" in allowed_hosts or "127.0.0.1" in allowed_hosts:
        return DEFAULT_LOCAL_CSRF_ORIGINS
    return ""


def parse_csrf_trusted_origins(raw_origins: str | None) -> list[str]:
    """
    Parse a comma-separated list of CSRF trusted origins.
    Strips whitespace, ignores empty entries, and strictly disallows wildcards ('*').
    """
    if not raw_origins:
        return []
    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip() and origin.strip() != "*"
    ]


default_csrf = get_default_csrf_trusted_origins(DEBUG, ALLOWED_HOSTS)
csrf_trusted_origins_str = os.environ.get("CSRF_TRUSTED_ORIGINS", default_csrf)
CSRF_TRUSTED_ORIGINS = parse_csrf_trusted_origins(csrf_trusted_origins_str)


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


# ============================================================
# SECURITY HEADERS & PRODUCTION HARDENING (Stage 18 & 22)
# ============================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Trusted Reverse Proxy SSL Header (Stage 22.2)
# Security Warning / Trust Assumption:
# ONLY enable SECURE_PROXY_SSL_HEADER when Django is running behind a trusted reverse proxy
# (e.g. Nginx, AWS ALB, Cloudflare, Render) that guarantees X-Forwarded-Proto is stripped
# from untrusted client requests and set correctly by the proxy.
# Do NOT enable this if Django is directly accessible by clients on the host or public internet,
# as clients could spoof the header and bypass HTTPS enforcement.
USE_SECURE_PROXY_SSL_HEADER = os.environ.get(
    "SECURE_PROXY_SSL_HEADER", "False"
).strip().lower() in ("true", "1", "yes")

if USE_SECURE_PROXY_SSL_HEADER:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    SECURE_PROXY_SSL_HEADER = None

SECURE_SSL_REDIRECT = os.environ.get(
    "SECURE_SSL_REDIRECT", "False"
).strip().lower() in ("true", "1")

SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE", "False"
).strip().lower() in ("true", "1")

CSRF_COOKIE_SECURE = os.environ.get(
    "CSRF_COOKIE_SECURE", "False"
).strip().lower() in ("true", "1")

SECURE_HSTS_SECONDS = int(
    os.environ.get("SECURE_HSTS_SECONDS", "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "False"
).strip().lower() in ("true", "1")
SECURE_HSTS_PRELOAD = os.environ.get(
    "SECURE_HSTS_PRELOAD", "False"
).strip().lower() in ("true", "1")

 