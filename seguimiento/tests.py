import json
import re
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Equipo, Prestamo, Rutina, Justificativo, Auditoria, Autorizacion


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
        self.assertContains(res_pista, 'data-pista-filter')
        self.assertContains(res_pista, 'data-pista-progress')
        self.assertContains(res_pista, 'data-mark-all-present')
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

    def test_player_portal_account_and_rut_login(self):
        data = {
            'rut': '11.111.112-K',
            'nombre_completo': 'Lucas Silva',
            'categoria': 'ESC',
            'fecha_nacimiento': '2015-03-10',
            'contacto_emergencia': '987654321',
            'observaciones': 'Inicio',
            'crear_cuenta': 'on',
        }
        res = self.client.post('/agregar/', data, follow=True)
        self.assertEqual(res.status_code, 200)
        player = Jugador.objects.get(rut='11.111.112-K')
        portal_user = User.objects.get(username='11.111.112-K')
        self.assertFalse(portal_user.is_staff)

        msg_text = ' '.join(str(m) for m in res.context['messages'])
        match = re.search(r'Contraseña temporal:\s*(\S+)', msg_text)
        self.assertIsNotNone(match)
        temp_password = match.group(1)

        # La clave temporal no debe quedar guardada en el registro de auditoría
        self.assertFalse(Auditoria.objects.filter(accion__icontains=temp_password).exists())

        self.client.logout()
        # Ingreso flexible sin puntos ni guión en minúscula
        login_res = self.client.post('/accounts/login/', {'username': '11111112k', 'password': temp_password})
        self.assertEqual(login_res.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), portal_user.pk)

        # Restricción: un alumno no puede acceder al reset ni crear accesos
        self.assertEqual(self.client.post(f'/jugadores/{player.pk}/acceso/').status_code, 403)

        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(f'/jugadores/{player.pk}/acceso/').status_code, 405)
        reset_res = self.client.post(f'/jugadores/{player.pk}/acceso/', follow=True)
        self.assertEqual(reset_res.status_code, 200)
        reset_msg = ' '.join(str(m) for m in reset_res.context['messages'])
        match2 = re.search(r'Contraseña temporal:\s*(\S+)', reset_msg)
        self.assertIsNotNone(match2)
        new_password = match2.group(1)
        self.assertNotEqual(new_password, temp_password)

        self.client.logout()
        self.assertEqual(
            self.client.post('/accounts/login/', {'username': '11.111.112-K', 'password': new_password}).status_code,
            302,
        )

    def test_password_change_flow(self):
        self.client.force_login(self.student)
        page = self.client.get('/accounts/password_change/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Cambiar contraseña')
        self.assertContains(page, 'seguimiento/css/styles.css')
        self.assertNotContains(page, 'Django administration')

        res = self.client.post(
            '/accounts/password_change/',
            {'old_password': 'test-pass', 'new_password1': 'HuaCh1pato#2026', 'new_password2': 'HuaCh1pato#2026'},
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Contraseña actualizada')
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('HuaCh1pato#2026'))

    def test_student_portal_chart_routines_and_justificativo(self):
        other_player = Jugador.objects.create(
            rut='999', nombre_completo='Otro Deportista', categoria='ESC', fecha_nacimiento='2014-05-05', contacto_emergencia='555'
        )
        s2 = ClaseEntrenamiento.objects.create(fecha=timezone.localdate())
        Evaluacion.objects.create(
            jugador=self.player,
            clase=self.session,
            asistencia='P',
            nota_frenado=8,
            nota_pase=7,
            nota_tiro=9,
            observacion_privada='PRIVADA_NO_ALUMNO',
        )
        eval_abs = Evaluacion.objects.create(jugador=self.player, clase=s2, asistencia='A')
        eval_other_abs = Evaluacion.objects.create(jugador=other_player, clase=s2, asistencia='A')

        r_own = Rutina.objects.create(
            jugador=self.player, titulo='Control bocha', objetivo='Dominio', ejercicios='3x10 min', fecha=timezone.localdate()
        )
        r_other = Rutina.objects.create(
            jugador=other_player, titulo='Rutina ajena', objetivo='Velocidad', ejercicios='Sprints', fecha=timezone.localdate()
        )

        self.client.force_login(self.student)
        home_res = self.client.get('/')
        self.assertEqual(home_res.status_code, 200)
        self.assertContains(home_res, 'seguimiento/js/history.js')
        self.assertContains(home_res, 'chart-data')
        self.assertNotContains(home_res, 'PRIVADA_NO_ALUMNO')
        self.assertNotContains(home_res, '<style>')

        # Completar rutina propia y bloqueo sobre rutina ajena
        self.assertEqual(self.client.post(f'/rutinas/{r_other.pk}/completar/').status_code, 404)
        r_other.refresh_from_db()
        self.assertFalse(r_other.completada)

        self.assertEqual(self.client.post(f'/rutinas/{r_own.pk}/completar/').status_code, 302)
        r_own.refresh_from_db()
        self.assertTrue(r_own.completada)

        # Justificativo del alumno: aislamiento estricto y estado forzado a pendiente
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            form_res = self.client.get('/mi-justificativo/')
            self.assertEqual(form_res.status_code, 200)
            self.assertNotContains(form_res, 'Otro Deportista')

            pdf = SimpleUploadedFile('cert.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
            bad_post = self.client.post('/mi-justificativo/', {'evaluacion': eval_other_abs.pk, 'motivo': 'Intento ajeno', 'archivo': pdf})
            self.assertEqual(bad_post.status_code, 200)
            self.assertFalse(Justificativo.objects.exists())

            pdf2 = SimpleUploadedFile('cert2.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
            ok_post = self.client.post(
                '/mi-justificativo/',
                {'evaluacion': eval_abs.pk, 'motivo': 'Reposo médico', 'archivo': pdf2, 'estado': 'aprobado'},
            )
            self.assertEqual(ok_post.status_code, 302)
            doc = Justificativo.objects.get()
            self.assertEqual(doc.estado, 'pendiente')
            self.assertContains(self.client.get('/'), 'Reposo médico')

    def test_filters_csv_exports_and_audit_log(self):
        p_esc = Jugador.objects.create(
            rut='=1+1', nombre_completo='=Malicioso Formula', categoria='ESC', fecha_nacimiento='2016-01-01', contacto_emergencia='111'
        )
        Evaluacion.objects.create(
            jugador=self.player,
            clase=self.session,
            categoria_registrada='S15',
            asistencia='P',
            nota_frenado=8,
            nota_pase=6,
            nota_tiro=7,
            observacion_privada='SECRETO_CSV',
        )
        Rutina.objects.create(jugador=self.player, titulo='Pendiente S15', objetivo='Pase', ejercicios='2x10', fecha=timezone.localdate(), completada=False)
        Rutina.objects.create(jugador=p_esc, titulo='Lista ESC', objetivo='Giro', ejercicios='2x10', fecha=timezone.localdate(), completada=True)

        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            pdf = SimpleUploadedFile('auth.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
            Autorizacion.objects.create(jugador=self.player, apoderado='Ana Prueba', fecha=timezone.localdate(), responsable='Coach', estado='vigente', archivo=pdf)

        # Filtros en listados
        res_players = self.client.get('/jugadores/', {'categoria': 'ESC'})
        self.assertContains(res_players, '=Malicioso Formula')
        self.assertNotContains(res_players, 'Jugador prueba')

        res_routines = self.client.get('/rutinas/', {'estado': 'completadas', 'categoria': 'ESC'})
        self.assertContains(res_routines, 'Lista ESC')
        self.assertNotContains(res_routines, 'Pendiente S15')

        res_auths = self.client.get('/autorizaciones/', {'estado': 'vigente', 'q': 'Ana'})
        self.assertContains(res_auths, 'Ana Prueba')

        # Exportación CSV de nómina con protección contra inyección de fórmulas y BOM UTF-8
        csv_players = self.client.get('/jugadores/exportar/', {'categoria': 'ESC'})
        self.assertEqual(csv_players.status_code, 200)
        self.assertTrue(csv_players['Content-Type'].startswith('text/csv'))
        body_players = csv_players.content.decode('utf-8-sig')
        self.assertIn("'=1+1", body_players)
        self.assertIn("'=Malicioso Formula", body_players)
        self.assertNotIn('Jugador prueba', body_players)

        # Exportación CSV mensual sin observaciones privadas
        csv_month = self.client.get('/reportes/', {'mes': timezone.localdate().strftime('%Y-%m'), 'jugador': self.player.pk, 'formato': 'csv'})
        self.assertEqual(csv_month.status_code, 200)
        self.assertTrue(csv_month['Content-Type'].startswith('text/csv'))
        body_month = csv_month.content.decode('utf-8-sig')
        self.assertIn('Jugador prueba', body_month)
        self.assertNotIn('SECRETO_CSV', body_month)

        # Auditoría
        audit_res = self.client.get('/auditoria/', {'q': 'Exportó'})
        self.assertEqual(audit_res.status_code, 200)
        self.assertContains(audit_res, 'Exportó')

        # Permisos: alumno bloqueado en CSV y auditoría
        self.client.force_login(self.student)
        self.assertEqual(self.client.get('/jugadores/exportar/').status_code, 403)
        self.assertEqual(self.client.get('/auditoria/').status_code, 403)
