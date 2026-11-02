"""Configuration Django. Les secrets sont lus depuis l'environnement."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables locales (.env puis .env.local) si python-dotenv est installé
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR / ".env.local", override=True)
except ImportError:
    pass


def env_list(name):
    """Lit une variable séparée par des virgules et retourne une liste propre."""
    return [x.strip().rstrip("/") for x in os.getenv(name, "").split(",") if x.strip()]


# Détection de l'environnement Vercel
ON_VERCEL = os.getenv("VERCEL", "").lower() == "1"

# Mode débogage : désactivé par défaut, activé seulement si demandé explicitement
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# Clé secrète : obligatoire en production, clé de développement seulement en DEBUG
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG and not ON_VERCEL:
        SECRET_KEY = "dev-only-change-this-key"
    else:
        raise ImproperlyConfigured(
            "Définissez DJANGO_SECRET_KEY dans les variables d'environnement."
        )

# Hôtes autorisés (ajoutez votre domaine ngrok dans DJANGO_ALLOWED_HOSTS si besoin)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
for host in env_list("DJANGO_ALLOWED_HOSTS"):
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Origines de confiance pour les formulaires (ex. https://xxxx.ngrok-free.dev)
CSRF_TRUSTED_ORIGINS = []
for origin in env_list("CSRF_TRUSTED_ORIGINS"):
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Domaines fournis automatiquement par Vercel
for vercel_host in (
    os.getenv("VERCEL_URL", ""),
    os.getenv("VERCEL_PROJECT_PRODUCTION_URL", ""),
):
    if vercel_host:
        host = vercel_host.removeprefix("https://").removeprefix("http://").rstrip("/")
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
        origin = f"https://{host}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)


# Applications Django
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "students.apps.StudentsConfig",
]

# Middleware (WhiteNoise sert les fichiers statiques en production)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "emsp_car.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "students.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "emsp_car.wsgi.application"


# Base de données : SQLite en local, PostgreSQL si DATABASE_URL est fourni
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Neon injecte généralement POSTGRES_URL dans Vercel. DATABASE_URL reste
# prioritaire pour les fournisseurs PostgreSQL classiques.
database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_URL_NON_POOLING")
    or ""
)

if ON_VERCEL and not database_url:
    raise ImproperlyConfigured(
        "Définissez DATABASE_URL (PostgreSQL persistant) avant de déployer."
    )

if database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(
        database_url,
        conn_max_age=0 if ON_VERCEL else 60,
        ssl_require=ON_VERCEL,
    )


# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Langue et fuseau horaire
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True


# Fichiers statiques : CSS, JavaScript et images
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}


# Configuration générale
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"


# Sécurité renforcée lorsque DEBUG est désactivé
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
