"""
Django settings for miproyecto project.

Configurado para desarrollo local (SQLite / private_media) y despliegue MVP
en Vercel + Supabase (PostgreSQL + Supabase Storage).
"""

import os
import ssl
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env si existe
load_dotenv(BASE_DIR / '.env')

IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-7do1n2cn$j(#juizm)-^f8n@brw2!#x(oiv*uw15$@b*$i1_k5',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False' if IS_VERCEL else 'True') == 'True'

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('ALLOWED_HOSTS', '.vercel.app,127.0.0.1,localhost').split(',')
    if h.strip()
]
if os.environ.get('VERCEL_URL') and os.environ['VERCEL_URL'] not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(os.environ['VERCEL_URL'])

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.vercel.app').split(',')
    if o.strip()
]
if os.environ.get('VERCEL_URL'):
    vercel_origin = f"https://{os.environ['VERCEL_URL']}"
    if vercel_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(vercel_origin)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'seguimiento',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'miproyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'miproyecto.wsgi.application'


# Database (PostgreSQL en Supabase vía DATABASE_URL, o SQLite en local)

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
DATABASE_URL = (
    os.environ.get('TEST_DATABASE_URL', '').strip()
    if TESTING and not IS_VERCEL
    else os.environ.get('DATABASE_URL', '').strip()
)


def _psycopg_disponible():
    try:
        import psycopg  # noqa: F401
        return True
    except ImportError:
        try:
            import psycopg2  # noqa: F401
            return True
        except ImportError:
            return False


if DATABASE_URL:
    is_postgres = DATABASE_URL.startswith(('postgres://', 'postgresql://'))
    is_pooler_tx = ':6543/' in DATABASE_URL
    db_config = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=0 if (IS_VERCEL or is_pooler_tx) else 600,
        conn_health_checks=not (IS_VERCEL or is_pooler_tx),
        ssl_require=is_postgres,
    )
    if db_config.get('ENGINE') == 'django.db.backends.postgresql':
        if is_pooler_tx:
            db_config['DISABLE_SERVER_SIDE_CURSORS'] = True
        if not _psycopg_disponible():
            try:
                import django_pg8000  # noqa: F401
            except ImportError:
                pass
            else:
                db_config['ENGINE'] = 'django_pg8000'
                sslmode = db_config.setdefault('OPTIONS', {}).pop('sslmode', None)
                if sslmode and sslmode != 'disable':
                    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE
                    db_config['OPTIONS']['ssl_context'] = ssl_ctx
    DATABASES = {'default': db_config}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = True


# Private Media & Storage (Supabase Storage en nube o disco local en desarrollo)

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'huachipato-media').strip()

MEDIA_ROOT = Path('/tmp/private_media') if IS_VERCEL else (BASE_DIR / 'private_media')

STORAGES = {
    'default': {
        'BACKEND': (
            'seguimiento.storage.SupabaseStorage'
            if (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}


# Email
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# Redirecciones del sistema de Login
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# Seguridad HTTPS en producción (Vercel / Proxy inverso)
if IS_VERCEL or os.environ.get('ENABLE_HTTPS_COOKIES') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
