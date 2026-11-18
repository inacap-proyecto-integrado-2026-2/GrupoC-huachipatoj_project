import json
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Autorizacion,
    ClaseEntrenamiento,
    Equipo,
    Evaluacion,
    Jugador,
    Justificativo,
    Prestamo,
    Rutina,
)
from .roles import ROL_ADMIN, ROL_ASISTENTE, ROL_ENTRENADOR, assign_staff_role

VALID_PDF = b'%PDF-1.4\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF'


class AccessControlTests(TestCase):
    def setUp(self):
        self.tmp_media = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_media.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.tmp_media.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        self.today = timezone.localdate()

        self.superuser = User.objects.create_user('ac_super', is_staff=True, is_superuser=True)
        self.admin = User.objects.create_user('ac_admin', is_staff=True)
        assign_staff_role(self.admin, ROL_ADMIN)

        self.coach = User.objects.create_user('ac_entrenador', is_staff=True)
        assign_staff_role(self.coach, ROL_ENTRENADOR)

        self.assistant = User.objects.create_user('ac_asistente', is_staff=True)
        assign_staff_role(self.assistant, ROL_ASISTENTE)

        self.player_a = Jugador.objects.create(
            rut='11.111.111-1',
            nombre_completo='Deportista Alpha',
            categoria='S15',
            fecha_nacimiento='2012-03-10',
            contacto_emergencia='911111111',
        )
        self.player_b = Jugador.objects.create(
            rut='22.222.222-2',
            nombre_completo='Deportista Beta',
            categoria='S15',
            fecha_nacimiento='2012-07-20',
            contacto_emergencia='922222222',
        )
        self.student_a = User.objects.create_user(
            self.player_a.rut, first_name=self.player_a.nombre_completo
        )
        self.student_b = User.objects.create_user(
            self.player_b.rut, first_name=self.player_b.nombre_completo
        )

        self.session_realized = ClaseEntrenamiento.objects.create(
            fecha=self.today,
            hora='18:00',
            categoria='S15',
            profesor='Entrenador',
            objetivo='Control de bocha',
            estado='realizada',
        )
        self.session_scheduled = ClaseEntrenamiento.objects.create(
            fecha=self.today + timedelta(days=3),
            hora='19:00',
            categoria='S15',
            profesor='Entrenador',
            objetivo='Definición',
            estado='programada',
        )
        self.eval_a = Evaluacion.objects.create(
            jugador=self.player_a,
            clase=self.session_realized,
            categoria_registrada='S15',
            asistencia='A',
            observacion_privada='OBSERVACION_CONFIDENCIAL_ALPHA',
        )
        self.doc_a = Justificativo.objects.create(
            evaluacion=self.eval_a,
            archivo=SimpleUploadedFile('just-a.pdf', VALID_PDF, content_type='application/pdf'),
            motivo='Reposo médico',
            estado='pendiente',
        )
        self.auth_a = Autorizacion.objects.create(
            jugador=self.player_a,
            apoderado='Apoderado Alpha',
            fecha=self.today,
            responsable='Entrenador',
            estado='vigente',
            archivo=SimpleUploadedFile('auth-a.pdf', VALID_PDF, content_type='application/pdf'),
        )
        self.equipment = Equipo.objects.create(codigo='EQ-AC-01', nombre='Patines RBAC', estado='bueno')
        self.loan = Prestamo.objects.create(equipo=self.equipment, jugador=self.player_a)
        self.routine_a = Rutina.objects.create(
            jugador=self.player_a,
            titulo='Rutina exclusiva Alpha',
            objetivo='Frenado en paralelo',
            ejercicios='3 series de 10 repeticiones',
            fecha=self.today + timedelta(days=1),
            completada=False,
        )

    def _staff_coach_get_urls(self):
        return [
            reverse('pista'),
            reverse('calendario'),
            reverse('programar_clase'),
            reverse('editar_clase', args=[self.session_scheduled.pk]),
            reverse('eliminar_clase', args=[self.session_scheduled.pk]),
            reverse('observacion', args=[self.eval_a.pk]),
            reverse('reportes'),
            reverse('jugadores'),
            reverse('historial', args=[self.player_a.pk]),
            reverse('inventario'),
            reverse('prestar', args=[self.equipment.pk]),
            reverse('rutinas'),
            reverse('nueva_rutina'),
            reverse('editar_rutina', args=[self.routine_a.pk]),
        ]

    def _titular_get_urls(self):
        return [
            reverse('exportar_jugadores'),
            reverse('agregar_jugador'),
            reverse('editar_jugador', args=[self.player_a.pk]),
            reverse('justificativos'),
            reverse('nuevo_justificativo'),
            reverse('archivo_justificativo', args=[self.doc_a.pk]),
            reverse('autorizaciones'),
            reverse('nueva_autorizacion'),
            reverse('editar_autorizacion', args=[self.auth_a.pk]),
            reverse('archivo_autorizacion', args=[self.auth_a.pk]),
            reverse('nuevo_equipo'),
            reverse('editar_equipo', args=[self.equipment.pk]),
            reverse('auditoria'),
        ]

    def _admin_get_urls(self):
        return [
            reverse('equipo_tecnico'),
            reverse('eliminar_cuenta', args=[self.student_b.pk]),
        ]

    def test_anonymous_users_redirected_on_all_protected_routes(self):
        all_protected_get = (
            [reverse('panel_entrenador'), reverse('mi_justificativo')]
            + self._staff_coach_get_urls()
            + self._titular_get_urls()
            + self._admin_get_urls()
        )
        for url in all_protected_get:
            with self.subTest(method='GET', url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 302)
                self.assertIn('/accounts/login/', resp['Location'])

        post_only_urls = [
            reverse('nueva_sesion'),
            reverse('guardar_evaluacion'),
            reverse('acceso_jugador', args=[self.player_a.pk]),
            reverse('revisar_justificativo', args=[self.doc_a.pk]),
            reverse('devolver', args=[self.loan.pk]),
            reverse('completar_rutina', args=[self.routine_a.pk]),
            reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]),
            reverse('eliminar_cuenta', args=[self.student_b.pk]),
        ]
        for url in post_only_urls:
            with self.subTest(method='POST', url=url):
                resp = self.client.post(url, {})
                self.assertEqual(resp.status_code, 302)
                self.assertIn('/accounts/login/', resp['Location'])

        # Public endpoints remain accessible and closed registration never creates accounts
        self.assertEqual(self.client.get(reverse('manifest')).status_code, 200)
        self.assertEqual(self.client.get(reverse('crear_cuenta')).status_code, 200)
        users_before = User.objects.count()
        self.assertEqual(
            self.client.post(reverse('crear_cuenta'), {'username': 'intruso', 'password': 'x'}).status_code,
            200,
        )
        self.assertEqual(User.objects.count(), users_before)

    def test_student_denied_all_staff_routes_get_and_post(self):
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get(reverse('panel_entrenador')).status_code, 200)
        self.assertEqual(self.client.get(reverse('mi_justificativo')).status_code, 200)

        denied_get = self._staff_coach_get_urls() + self._titular_get_urls() + self._admin_get_urls()
        for url in denied_get:
            with self.subTest(method='GET', url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

        denied_post = [
            (reverse('nueva_sesion'), {}),
            (
                reverse('guardar_evaluacion'),
                json.dumps({'jugador': self.player_a.pk, 'sesion': self.session_realized.pk, 'asistencia': 'P'}),
                'application/json',
            ),
            (reverse('eliminar_clase', args=[self.session_scheduled.pk]), {}),
            (reverse('acceso_jugador', args=[self.player_b.pk]), {'accion': 'crear'}),
            (reverse('revisar_justificativo', args=[self.doc_a.pk]), {'estado': 'aprobado'}),
            (reverse('devolver', args=[self.loan.pk]), {'estado': 'bueno'}),
            (reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]), {'action': 'toggle'}),
            (reverse('eliminar_cuenta', args=[self.student_b.pk]), {'confirmacion': self.student_b.username}),
        ]
        for entry in denied_post:
            url, payload = entry[0], entry[1]
            kwargs = {'content_type': entry[2]} if len(entry) == 3 else {}
            with self.subTest(method='POST', url=url):
                self.assertEqual(self.client.post(url, payload, **kwargs).status_code, 403)

        self.assertTrue(ClaseEntrenamiento.objects.filter(pk=self.session_scheduled.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.student_b.pk).exists())
        self.doc_a.refresh_from_db()
        self.assertEqual(self.doc_a.estado, 'pendiente')

    def test_assistant_rbac_boundary_allowed_and_denied(self):
        self.client.force_login(self.assistant)

        for url in [reverse('panel_entrenador')] + self._staff_coach_get_urls():
            with self.subTest(allowed_url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        for url in self._titular_get_urls() + self._admin_get_urls():
            with self.subTest(denied_get=url):
                self.assertEqual(self.client.get(url).status_code, 403)

        denied_posts = [
            (reverse('acceso_jugador', args=[self.player_a.pk]), {'accion': 'reset'}),
            (reverse('revisar_justificativo', args=[self.doc_a.pk]), {'estado': 'aprobado'}),
            (reverse('gestionar_equipo_tecnico', args=[self.coach.pk]), {'action': 'toggle'}),
            (reverse('eliminar_cuenta', args=[self.student_b.pk]), {'confirmacion': self.student_b.username}),
        ]
        for url, data in denied_posts:
            with self.subTest(denied_post=url):
                self.assertEqual(self.client.post(url, data).status_code, 403)

    def test_coach_titular_rbac_boundary_allowed_and_denied(self):
        self.client.force_login(self.coach)

        for url in self._titular_get_urls():
            with self.subTest(allowed_titular=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)
                if hasattr(resp, 'close'):
                    resp.close()

        for url in self._admin_get_urls():
            with self.subTest(denied_admin_get=url):
                self.assertEqual(self.client.get(url).status_code, 403)

        self.assertEqual(
            self.client.post(reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]), {'action': 'toggle'}).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('eliminar_cuenta', args=[self.student_b.pk]), {'confirmacion': self.student_b.username}
            ).status_code,
            403,
        )

    def test_club_admin_and_superuser_privilege_hierarchy(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('equipo_tecnico')).status_code, 200)

        # Club admin cannot modify, toggle, reset, or delete a superuser
        for action_data in ({'action': 'role', 'rol': ROL_ASISTENTE}, {'action': 'toggle'}, {'action': 'reset'}):
            with self.subTest(action=action_data['action']):
                self.assertEqual(
                    self.client.post(reverse('gestionar_equipo_tecnico', args=[self.superuser.pk]), action_data).status_code,
                    403,
                )
        self.assertEqual(
            self.client.post(
                reverse('eliminar_cuenta', args=[self.superuser.pk]), {'confirmacion': self.superuser.username}
            ).status_code,
            403,
        )
        # Club admin cannot self-delete or self-deactivate
        self.assertEqual(
            self.client.post(
                reverse('eliminar_cuenta', args=[self.admin.pk]), {'confirmacion': self.admin.username}
            ).status_code,
            403,
        )
        self.client.post(reverse('gestionar_equipo_tecnico', args=[self.admin.pk]), {'action': 'toggle'})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

        # Club admin CAN change role of non-superuser staff
        self.assertRedirects(
            self.client.post(
                reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]),
                {'action': 'role', 'rol': ROL_ENTRENADOR},
            ),
            reverse('equipo_tecnico'),
        )
        self.assertTrue(self.assistant.groups.filter(name=ROL_ENTRENADOR).exists())

        # Superuser still cannot delete itself
        self.client.force_login(self.superuser)
        self.assertEqual(
            self.client.post(
                reverse('eliminar_cuenta', args=[self.superuser.pk]), {'confirmacion': self.superuser.username}
            ).status_code,
            403,
        )

    def test_horizontal_isolation_between_students_anti_idor(self):
        # Student B cannot view Student A's data or private coach observation
        self.client.force_login(self.student_b)
        portal_b = self.client.get(reverse('panel_entrenador'))
        self.assertEqual(portal_b.status_code, 200)
        self.assertNotContains(portal_b, self.player_a.nombre_completo)
        self.assertNotContains(portal_b, self.routine_a.titulo)
        self.assertNotContains(portal_b, 'OBSERVACION_CONFIDENCIAL_ALPHA')

        # Student B cannot complete Student A's routine (IDOR -> 404)
        resp_routine = self.client.post(reverse('completar_rutina', args=[self.routine_a.pk]))
        self.assertEqual(resp_routine.status_code, 404)
        self.routine_a.refresh_from_db()
        self.assertFalse(self.routine_a.completada)

        # Student B cannot upload a justificativo referencing Student A's evaluation
        docs_before = Justificativo.objects.count()
        resp_doc = self.client.post(
            reverse('mi_justificativo'),
            {
                'evaluacion': self.eval_a.pk,
                'motivo': 'Intento cruzado',
                'archivo': SimpleUploadedFile('cross.pdf', VALID_PDF, content_type='application/pdf'),
            },
        )
        self.assertEqual(resp_doc.status_code, 200)
        self.assertIn('evaluacion', resp_doc.context['form'].errors)
        self.assertEqual(Justificativo.objects.count(), docs_before)

        # Even Student A cannot see private coach observation or access staff download endpoints
        self.client.force_login(self.student_a)
        portal_a = self.client.get(reverse('panel_entrenador'))
        self.assertContains(portal_a, self.routine_a.titulo)
        self.assertNotContains(portal_a, 'OBSERVACION_CONFIDENCIAL_ALPHA')
        self.assertEqual(self.client.get(reverse('archivo_justificativo', args=[self.doc_a.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('archivo_autorizacion', args=[self.auth_a.pk])).status_code, 403)

    def test_deactivated_account_blocked_from_login_and_existing_session(self):
        self.student_a.set_password('Access#Password1')
        self.student_a.save(update_fields=['password'])
        logged_client = Client()
        self.assertTrue(logged_client.login(username=self.student_a.username, password='Access#Password1'))
        self.assertEqual(logged_client.get(reverse('panel_entrenador')).status_code, 200)

        self.student_a.is_active = False
        self.student_a.save(update_fields=['is_active'])

        # Existing session loses access immediately
        resp = logged_client.get(reverse('panel_entrenador'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])

        # Fresh login fails
        fresh_client = Client()
        self.assertFalse(fresh_client.login(username=self.student_a.username, password='Access#Password1'))

    def test_post_only_endpoints_reject_get_with_405(self):
        self.client.force_login(self.admin)
        staff_post_only = [
            reverse('nueva_sesion'),
            reverse('guardar_evaluacion'),
            reverse('acceso_jugador', args=[self.player_a.pk]),
            reverse('revisar_justificativo', args=[self.doc_a.pk]),
            reverse('devolver', args=[self.loan.pk]),
            reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]),
        ]
        for url in staff_post_only:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get(reverse('completar_rutina', args=[self.routine_a.pk])).status_code, 405)

    def test_csrf_enforced_on_sensitive_state_changes(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)

        sensitive_posts = [
            (
                reverse('guardar_evaluacion'),
                json.dumps({'jugador': self.player_a.pk, 'sesion': self.session_realized.pk, 'asistencia': 'P'}),
                'application/json',
            ),
            (reverse('revisar_justificativo', args=[self.doc_a.pk]), {'estado': 'aprobado'}),
            (reverse('acceso_jugador', args=[self.player_a.pk]), {'accion': 'reset'}),
            (reverse('gestionar_equipo_tecnico', args=[self.assistant.pk]), {'action': 'toggle'}),
            (reverse('eliminar_cuenta', args=[self.student_b.pk]), {'confirmacion': self.student_b.username}),
            (reverse('eliminar_clase', args=[self.session_scheduled.pk]), {}),
        ]
        for entry in sensitive_posts:
            url, payload = entry[0], entry[1]
            kwargs = {'content_type': entry[2]} if len(entry) == 3 else {}
            with self.subTest(url=url):
                self.assertEqual(csrf_client.post(url, payload, **kwargs).status_code, 403)
