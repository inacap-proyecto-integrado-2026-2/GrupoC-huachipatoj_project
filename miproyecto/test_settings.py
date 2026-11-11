"""Configuración aislada: nunca carga .env ni utiliza servicios de producción."""
import os
from unittest.mock import patch

_local_env = {
    'LOCAL_SQLITE': '1', 'DEBUG': 'False',
    'SECRET_KEY': 'clave-exclusiva-pruebas-locales-no-produccion',
}
with patch.dict(os.environ, _local_env, clear=True), patch('dotenv.load_dotenv'):
    from .settings import *  # noqa: F403,F401

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:',
    'TEST': {'NAME': ':memory:'},
}}
MEDIA_ROOT = os.environ['HUACHIPATO_TEST_MEDIA']
STORAGES['default'] = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
USE_SUPABASE_STORAGE = False
SUPABASE_URL = ''
SUPABASE_SERVICE_ROLE_KEY = ''
