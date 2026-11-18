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

    def test_calendar_extreme_dates_show_validation(self):
        for mode in ('mes', 'semana', 'lista'):
            for value in ('0001-01-01', '9999-12-31', 'abc', '2026-02-30'):
                with self.subTest(mode=mode, value=value):
                    response = self.client.get('/calendario/', {'fecha': value, 'vista': mode})
                    self.assertContains(response, 'Fecha inválida o fuera del rango')

    def test_extreme_class_dates_do_not_create_partial_series(self):
        for value in ('9999-12-31', '0001-01-01', '9998-12-31'):
            response = self.client.post('/clases/nueva/', dict(fecha=value, hora='18:00', categoria='S15', profesor='Prueba', objetivo='Prueba', estado='programada', semanas=12))
            self.assertContains(response, 'entre los años 2 y 9998')
        self.assertEqual(ClaseEntrenamiento.objects.count(), 0)
