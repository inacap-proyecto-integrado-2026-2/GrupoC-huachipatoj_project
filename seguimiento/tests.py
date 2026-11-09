import json
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Equipo, Prestamo, Rutina, Justificativo, Autorizacion


class PilotTests(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user('coach', password='test-pass', is_staff=True)
        self.student = User.objects.create_user('123', password='test-pass')
        self.player = Jugador.objects.create(rut='123', nombre_completo='Jugador prueba', fecha_nacimiento='2010-01-01', contacto_emergencia='123456789')
        self.session = ClaseEntrenamiento.objects.create()
        self.client.force_login(self.coach)

    def test_pages(self):
        for url in ['/', '/pista/', '/jugadores/', '/agregar/', f'/jugadores/{self.player.pk}/', f'/jugadores/{self.player.pk}/editar/', '/justificativos/', '/justificativos/nuevo/', '/inventario/', '/inventario/nuevo/', '/rutinas/', '/rutinas/nueva/', '/accounts/login/', '/registro/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_scores_persist_and_validate(self):
        data = dict(jugador=self.player.pk, sesion=self.session.pk, asistencia='P', nota_frenado=8, nota_pase=7, nota_tiro=9)
        self.assertEqual(self.client.post('/evaluaciones/guardar/', data=json.dumps(data), content_type='application/json').status_code, 200)
        self.assertEqual(Evaluacion.objects.get().nota_frenado, 8)
        self.assertContains(self.client.get('/pista/'), 'data-value="8"')
        self.assertContains(self.client.get(f'/?sesion={self.session.pk}'), 'data-value="8"')
        data['nota_tiro'] = 11
        self.assertEqual(self.client.post('/evaluaciones/guardar/', data=json.dumps(data), content_type='application/json').status_code, 400)
        self.assertEqual(Evaluacion.objects.get().nota_tiro, 9)
        data.update(asistencia='A', nota_tiro=9)
        self.client.post('/evaluaciones/guardar/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(Evaluacion.objects.get().nota_tiro, 0)

    def test_permissions(self):
        self.client.force_login(self.student)
        for url in ['/jugadores/', '/agregar/', '/inventario/', '/justificativos/', '/rutinas/']:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post('/evaluaciones/guardar/', '{}', content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get('/').status_code, 302)

    def test_inventory_loan_return(self):
        self.client.post('/inventario/nuevo/', {'codigo': 'P01', 'nombre': 'Patines', 'estado': 'bueno'})
        equipment = Equipo.objects.get()
        url = f'/inventario/{equipment.pk}/prestar/'
        self.assertEqual(self.client.post(url, {'jugador': self.player.pk}).status_code, 302)
        self.assertEqual(self.client.post(url, {'jugador': self.player.pk}).status_code, 200)
        self.assertEqual(Prestamo.objects.count(), 1)
        p = Prestamo.objects.get()
        self.assertEqual(self.client.get(f'/prestamos/{p.pk}/devolver/').status_code, 405)
        self.client.post(f'/prestamos/{p.pk}/devolver/')
        p.refresh_from_db()
        self.assertIsNotNone(p.devuelto)
        self.assertEqual(self.client.post(url, {'jugador': self.player.pk}).status_code, 302)
        self.assertContains(self.client.get('/inventario/?pendientes=1'), 'Patines')

    def test_documents_and_review(self):
        e = Evaluacion.objects.create(jugador=self.player, clase=self.session, asistencia='A')
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            bad = SimpleUploadedFile('fake.pdf', b'not a pdf')
            self.client.post('/justificativos/nuevo/', {'evaluacion': e.pk, 'motivo': 'Reposo', 'archivo': bad})
            self.assertFalse(Justificativo.objects.exists())
            pdf = SimpleUploadedFile('certificado.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
            self.assertEqual(self.client.post('/justificativos/nuevo/', {'evaluacion': e.pk, 'motivo': 'Reposo', 'archivo': pdf}).status_code, 302)
            d = Justificativo.objects.get()
            response = self.client.get(f'/justificativos/{d.pk}/archivo/')
            self.assertEqual(response.status_code, 200)
            response.close()
            self.client.post(f'/justificativos/{d.pk}/revisar/', {'estado': 'aprobado'})
            e.refresh_from_db()
            self.assertEqual(e.asistencia, 'J')
            self.client.force_login(self.student)
            self.assertEqual(self.client.get(f'/justificativos/{d.pk}/archivo/').status_code, 403)

    def test_routine_and_student_isolation(self):
        data = {'jugador': self.player.pk, 'titulo': 'Tiro', 'objetivo': 'Precisión', 'ejercicios': 'Tres series de diez tiros', 'fecha': '2026-09-30', 'observaciones': ''}
        self.assertEqual(self.client.post('/rutinas/nueva/', data).status_code, 302)
        r = Rutina.objects.get()
        data.update(completada='on', observaciones='Mejoró precisión')
        self.client.post(f'/rutinas/{r.pk}/editar/', data)
        r.refresh_from_db()
        self.assertTrue(r.completada)
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/'), 'Mejoró precisión')
        other = User.objects.create_user('other')
        self.client.force_login(other)
        self.assertNotContains(self.client.get('/'), 'Mejoró precisión')

    def test_create_update_player(self):
        data = {'rut': '12.345.678-5', 'nombre_completo': 'Nuevo jugador', 'categoria': 'ESC', 'fecha_nacimiento': '2014-02-03', 'contacto_emergencia': '987654321', 'observaciones': 'Inicial'}
        self.assertEqual(self.client.post('/agregar/', data).status_code, 302)
        p = Jugador.objects.get(rut='12.345.678-5')
        data['categoria'] = 'S15'
        self.client.post(f'/jugadores/{p.pk}/editar/', data)
        p.refresh_from_db()
        self.assertEqual(p.categoria, 'S15')
        data['rut'] = '11.111.111-1'
        self.client.post(f'/jugadores/{p.pk}/editar/', data)
        p.refresh_from_db()
        self.assertEqual(p.rut, '12.345.678-5')

    def test_rut_modulo_11_validation(self):
        base = {'nombre_completo': 'Jugador Rut', 'categoria': 'ESC', 'fecha_nacimiento': '2014-02-03', 'contacto_emergencia': '987654321', 'observaciones': ''}
        for bad_rut in ['456', '12.345.678-9', '00000000-0', 'abc1234-5']:
            res = self.client.post('/agregar/', {**base, 'rut': bad_rut})
            self.assertEqual(res.status_code, 200)
            self.assertFalse(Jugador.objects.filter(nombre_completo='Jugador Rut').exists())

        res = self.client.post('/agregar/', {**base, 'rut': '11111112k'})
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Jugador.objects.filter(rut='11.111.112-K').exists())

        res_dup = self.client.post('/agregar/', {**base, 'rut': '11111112-K'})
        self.assertEqual(res_dup.status_code, 200)
        self.assertEqual(Jugador.objects.filter(rut='11.111.112-K').count(), 1)

        demo = Jugador.objects.create(rut='DEMO-999', nombre_completo='Demo Test', categoria='ESC', fecha_nacimiento='2015-01-01', contacto_emergencia='123')
        res_demo = self.client.post(f'/jugadores/{demo.pk}/editar/', {**base, 'rut': 'DEMO-999', 'categoria': 'S15'})
        self.assertEqual(res_demo.status_code, 302)
        demo.refresh_from_db()
        self.assertEqual(demo.categoria, 'S15')

    def test_static_assets_separated_from_html(self):
        res_home = self.client.get('/')
        self.assertContains(res_home, 'seguimiento/css/styles.css')
        self.assertContains(res_home, 'seguimiento/js/layout.js')
        self.assertContains(res_home, 'app-sidebar')
        self.assertNotContains(res_home, '<style>')
        res_pista = self.client.get('/pista/')
        self.assertContains(res_pista, 'seguimiento/js/pista.js')
        self.assertNotContains(res_pista, '<style>')
        res_hist = self.client.get(f'/jugadores/{self.player.pk}/')
        self.assertContains(res_hist, 'seguimiento/js/history.js')

    def test_dashboard_metrics_and_sidebar_badges(self):
        ev = Evaluacion.objects.create(jugador=self.player, clase=self.session, asistencia='A')
        Justificativo.objects.create(evaluacion=ev, motivo='Control médico', estado='pendiente')
        Autorizacion.objects.create(jugador=self.player, apoderado='Apoderado', fecha='2026-10-01', responsable='Coach', estado='pendiente')
        eq = Equipo.objects.create(codigo='EQ-1', nombre='Casco', estado='bueno')
        Prestamo.objects.create(equipo=eq, jugador=self.player)

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Panel de control')
        self.assertContains(res, 'Control médico')
        self.assertContains(res, 'Casco')
        self.assertEqual(res.context['nav_pending_docs'], 1)
        self.assertEqual(res.context['nav_pending_auth'], 1)
        self.assertEqual(res.context['nav_active_loans'], 1)

    def test_supabase_storage_backend(self):
        import urllib.error
        from unittest.mock import MagicMock, patch
        from django.core.files.base import ContentFile
        from .storage import SupabaseStorage

        storage = SupabaseStorage(base_url='https://demo.supabase.co', service_key='secret-key', bucket='privado')
        uploaded = {}

        def fake_urlopen(req, timeout=20):
            method = req.get_method()
            if method == 'HEAD':
                if req.full_url in uploaded:
                    resp = MagicMock()
                    resp.status = 200
                    resp.__enter__.return_value = resp
                    return resp
                raise urllib.error.HTTPError(req.full_url, 404, 'Not Found', {}, None)
            if method == 'POST':
                uploaded[req.full_url.replace('/object/', '/object/authenticated/')] = req.data
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = uploaded.get(req.full_url, b'')
            resp.__enter__.return_value = resp
            return resp

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            saved = storage.save('justificativos/test.pdf', ContentFile(b'%PDF-1.4\n%%EOF'))
            self.assertEqual(saved, 'justificativos/test.pdf')
            self.assertTrue(storage.exists('justificativos/test.pdf'))

            opened = storage.open('justificativos/test.pdf', 'rb')
            self.assertEqual(opened.read(), b'%PDF-1.4\n%%EOF')

            storage.delete('justificativos/test.pdf')

        with self.assertRaises(NotImplementedError):
            storage.url('justificativos/test.pdf')

    def test_demo_is_repeatable_and_preserves_edits(self):
        from django.core.management import call_command
        from io import StringIO
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            call_command('cargar_demo', stdout=StringIO())
            self.assertEqual(Jugador.objects.filter(rut__startswith='DEMO-').count(), 18)
            self.assertEqual(Justificativo.objects.count(), 9)
            p = Jugador.objects.get(rut='DEMO-001')
            p.observaciones = 'Cambio del entrenador'
            p.save()
            counts = [m.objects.count() for m in [Jugador, ClaseEntrenamiento, Evaluacion, Rutina, Equipo, Prestamo, Justificativo]]
            call_command('cargar_demo', stdout=StringIO())
            self.assertEqual(counts, [m.objects.count() for m in [Jugador, ClaseEntrenamiento, Evaluacion, Rutina, Equipo, Prestamo, Justificativo]])
            p.refresh_from_db()
            self.assertEqual(p.observaciones, 'Cambio del entrenador')
