from django.contrib.auth.models import User
from django.test import TestCase
from .models import ClaseEntrenamiento


class InputSecurityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('seguridad', is_staff=True)
        self.client.force_login(self.staff)

    def test_invalid_session_identifiers(self):
        for url in ('/pista/', '/'):
            for value in ('abc', "' OR 1=1 --", '9' * 1000, '-1', '0', '1.5', '²'):
                with self.subTest(url=url, value=value[:20]):
                    self.assertEqual(self.client.get(url, {'sesion': value}).status_code, 400)

    def test_existing_and_missing_session(self):
        session = ClaseEntrenamiento.objects.create()
        self.assertEqual(self.client.get('/pista/', {'sesion': session.pk}).status_code, 200)
        self.assertEqual(self.client.get('/pista/', {'sesion': session.pk + 1}).status_code, 404)
