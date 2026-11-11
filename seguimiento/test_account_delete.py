from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Rutina, Auditoria
from .roles import assign_staff_role, ROL_ADMIN, ROL_ENTRENADOR, ROL_ASISTENTE


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin-club', is_staff=True)
        assign_staff_role(self.admin, ROL_ADMIN)
        self.target = User.objects.create_user('DEMO-DELETE')
        self.url = reverse('eliminar_cuenta', args=[self.target.pk])
        self.client.force_login(self.admin)

    def test_admin_deletes_access_but_preserves_sports_history(self):
        player = Jugador.objects.create(rut=self.target.username, nombre_completo='Prueba', fecha_nacimiento='2010-01-01', contacto_emergencia='123')
        evaluation = Evaluacion.objects.create(jugador=player, clase=ClaseEntrenamiento.objects.create())
        routine = Rutina.objects.create(jugador=player, titulo='Prueba', objetivo='Prueba', ejercicios='Prueba', fecha='2026-01-01')
        audit = Auditoria.objects.create(usuario=self.target, accion='Historial previo')
        student_client = Client()
        student_client.force_login(self.target)
        self.assertRedirects(self.client.post(self.url, {'confirmacion': self.target.username}), reverse('equipo_tecnico'))
        self.assertFalse(User.objects.filter(pk=self.target.pk).exists())
        for obj in (player, evaluation, routine, audit):
            obj.refresh_from_db()
        self.assertIsNone(audit.usuario_id)
        self.assertTrue(Auditoria.objects.filter(usuario=self.admin, accion__startswith='Eliminó cuenta').exists())
        self.assertEqual(student_client.get('/').status_code, 302)

    def test_get_and_incorrect_confirmation_never_delete(self):
        self.assertContains(self.client.get(self.url), 'Eliminar cuenta definitivamente')
        for value in ('', 'otro'):
            self.assertEqual(self.client.post(self.url, {'confirmacion': value}).status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())

    def test_non_admin_roles_are_denied_even_with_direct_post(self):
        for role in (ROL_ENTRENADOR, ROL_ASISTENTE, None):
            actor = User.objects.create_user('actor-' + str(role), is_staff=role is not None)
            if role:
                assign_staff_role(actor, role)
            self.client.force_login(actor)
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(self.url, {'confirmacion': self.target.username}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'confirmacion': self.target.username}).status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())

    def test_self_and_superuser_are_protected(self):
        superuser = User.objects.create_user('super', is_staff=True, is_superuser=True)
        for actor in (self.admin, superuser):
            self.client.force_login(actor)
            for target in (actor, superuser):
                self.assertEqual(self.client.post(reverse('eliminar_cuenta', args=[target.pk]), {'confirmacion': target.username}).status_code, 403)
                self.assertTrue(User.objects.filter(pk=target.pk).exists())

    def test_staff_deletion_and_account_list(self):
        self.target.is_staff = True
        self.target.save()
        assign_staff_role(self.target, ROL_ENTRENADOR)
        self.assertContains(self.client.get(reverse('equipo_tecnico')), self.url)
        self.client.post(self.url, {'confirmacion': self.target.username})
        self.assertFalse(User.objects.filter(pk=self.target.pk).exists())

    def test_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url, {'confirmacion': self.target.username}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())
