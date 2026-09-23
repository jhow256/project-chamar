import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VALIDATION_SQLITE = os.environ.get("VALIDATION_SQLITE") == "1"
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-secret-key-change-in-production-2026",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [x for x in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if x]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "rest_framework_simplejwt.token_blacklist",
    "django_filters", "drf_spectacular", "core", "organization", "accounts",
    "tickets", "dashboard", "audit",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request",
              "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if VALIDATION_SQLITE:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "validation.sqlite3"}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.environ.get("POSTGRES_DB", "chamar"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"), "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"), "PORT": os.environ.get("POSTGRES_PORT", "5432")}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Manaus"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "private_media"
MEDIA_URL = "/media/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher", "django.contrib.auth.hashers.PBKDF2PasswordHasher"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend", "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {"login": "5/min", "password_reset": "3/hour"},
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
              "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True}
SPECTACULAR_SETTINGS = {
    "TITLE": "Chamar API",
    "DESCRIPTION": "Sistema de chamados de TI",
    "VERSION": "1.0.0",
    "ENUM_NAME_OVERRIDES": {"PriorityEnum": "tickets.models.Ticket.Priority"},
}
CORS_ALLOWED_ORIGINS = [x.strip() for x in os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
).split(",") if x.strip()]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [x for x in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if x]
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "nao-responda@chamar.local")
REFRESH_COOKIE_SECURE = os.environ.get("REFRESH_COOKIE_SECURE", "1" if not DEBUG else "0") == "1"
AUDIT_IP_SALT = os.environ.get("AUDIT_IP_SALT", SECRET_KEY)
TRUST_X_FORWARDED_FOR = os.environ.get("TRUST_X_FORWARDED_FOR", "0") == "1"
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {"django.server": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}
