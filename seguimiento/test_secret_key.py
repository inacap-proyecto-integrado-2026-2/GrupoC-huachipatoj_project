import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.test import SimpleTestCase


class SecretKeyConfigurationTests(SimpleTestCase):
    def load_settings(self, **env):
        path = Path(__file__).resolve().parents[1] / 'miproyecto' / 'settings.py'
        with patch.dict(os.environ, env, clear=True), patch('dotenv.load_dotenv'):
            return runpy.run_path(str(path))

    def test_production_rejects_missing_and_weak_keys(self):
        for key in (None, '', ' ' * 60, 'corta', 'x' * 60,
                    'django-insecure-' + get_random_secret_key(),
                    'cambia-esta-clave-por-una-larga-y-aleatoria'):
            with self.subTest(case='missing' if key is None else 'weak'):
                env = {'DEBUG': 'False'}
                if key is not None:
                    env['SECRET_KEY'] = key
                with self.assertRaises(ImproperlyConfigured):
                    self.load_settings(**env)

    def test_vercel_rejects_missing_key_even_with_debug(self):
        for marker in ({'VERCEL': '1'}, {'VERCEL_ENV': 'preview'}, {'VERCEL_ENV': 'production'}):
            with self.subTest(marker=marker), self.assertRaises(ImproperlyConfigured):
                self.load_settings(DEBUG='True', **marker)

    def test_valid_key_is_preserved_exactly(self):
        key = get_random_secret_key()
        for env in ({'DEBUG': 'False'}, {'VERCEL': '1'}):
            with self.subTest(env=env):
                self.assertEqual(self.load_settings(SECRET_KEY=key, **env)['SECRET_KEY'], key)

    def test_local_development_still_starts(self):
        self.assertTrue(self.load_settings()['SECRET_KEY'])
        self.assertEqual(self.load_settings(DEBUG='True', SECRET_KEY='local-only')['SECRET_KEY'], 'local-only')

    def test_error_does_not_disclose_value(self):
        key = 'valor-secreto-invalido'
        with self.assertRaises(ImproperlyConfigured) as error:
            self.load_settings(DEBUG='False', SECRET_KEY=key)
        self.assertNotIn(key, str(error.exception))
