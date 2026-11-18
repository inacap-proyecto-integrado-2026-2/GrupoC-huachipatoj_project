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

    def test_long_text_and_quotes_are_validated(self):
        data = dict(fecha='2026-11-18', hora='18:00', categoria='S15', profesor='Prueba', objetivo='x' * 251, estado='programada')
        response = self.client.post('/clases/nueva/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(ClaseEntrenamiento.objects.exists())
        data['objetivo'] = "Pase 'controlado' y <script>alert(1)</script>"
        self.assertEqual(self.client.post('/clases/nueva/', data).status_code, 302)
        response = self.client.get('/calendario/', {'fecha': data['fecha']})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_malformed_score_payloads_never_change_data(self):
        from .models import Evaluacion
        for payload in ('{', '[]', 'null', '{"asistencia":"P"}', '{"asistencia":"P","nota_frenado":"' + 'x' * 10000 + '"}'):
            with self.subTest(payload=payload[:30]):
                self.assertEqual(self.client.post('/evaluaciones/guardar/', data=payload, content_type='application/json').status_code, 400)
        self.assertFalse(Evaluacion.objects.exists())

    def test_reviewed_document_cannot_be_reopened_or_reversed(self):
        from .models import Jugador, Evaluacion, Justificativo
        player = Jugador.objects.create(rut='DEMO-SEC', nombre_completo='Prueba', fecha_nacimiento='2010-01-01', contacto_emergencia='123')
        evaluation = Evaluacion.objects.create(jugador=player, clase=ClaseEntrenamiento.objects.create(), asistencia='J')
        doc = Justificativo.objects.create(evaluacion=evaluation, archivo='ficticio.pdf', motivo='Prueba', estado='aprobado', revisado_por=self.staff, observacion_revision='Cerrado')
        response = self.client.post(f'/justificativos/{doc.pk}/revisar/', {'estado':'rechazado', 'observacion_revision':'Intento de modificar'})
        self.assertEqual(response.status_code, 302)
        doc.refresh_from_db(); evaluation.refresh_from_db()
        self.assertEqual(doc.estado, 'aprobado')
        self.assertEqual(doc.observacion_revision, 'Cerrado')
        self.assertEqual(evaluation.asistencia, 'J')
