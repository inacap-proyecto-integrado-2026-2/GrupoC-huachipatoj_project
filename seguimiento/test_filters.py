from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from .filters import apply_filters
from .models import Jugador, Rutina, ClaseEntrenamiento, Equipo, Prestamo

class FilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.player = Jugador.objects.create(rut='DEMO-F', nombre_completo='Filtro', fecha_nacimiento='2010-01-01', contacto_emergencia='123')
        self.staff = User.objects.create_user('staff', is_staff=True)
        self.client.force_login(self.staff)

    def test_date_boundaries_and_overdue(self):
        today = timezone.localdate()
        for offset in (-1, 0, 1):
            Rutina.objects.create(jugador=self.player, titulo=str(offset), ejercicios='x', objetivo='x', fecha=today + timedelta(days=offset))
        for params, expected in [({'desde':str(today),'hasta':str(today)},1), ({'vencidas':'on'},1), ({'desde':'mal'},0), ({'desde':str(today),'hasta':str(today-timedelta(days=1))},0)]:
            rows, form = apply_filters(self.factory.get('/',params),Rutina.objects.all(),'routines')
            self.assertEqual(rows.count(), expected)

    def test_accounts_and_csv_match(self):
        User.objects.create_user(self.player.rut, is_active=False)
        for value, count in [('activa',0),('desactivada',1),('sin',0)]:
            params={'cuenta':value,'q':'Filtro','categoria':self.player.categoria}
            response=self.client.get('/jugadores/',params)
            self.assertEqual(len(response.context['jugadores']),count)
            csv=self.client.get('/jugadores/exportar/',params).content.decode('utf-8')
            self.assertEqual('Filtro' in csv, bool(count))

    def test_inventory_and_calendar_combined_filters(self):
        item=Equipo.objects.create(codigo='X',nombre='Patines',estado='desgastado')
        Prestamo.objects.create(equipo=item,jugador=self.player)
        for availability, expected in [('prestado',1),('libre',0)]:
            rows,_=apply_filters(self.factory.get('/',{'condicion':'desgastado','disponibilidad':availability}),Equipo.objects.all(),'inventory')
            self.assertEqual(rows.count(),expected)
        ClaseEntrenamiento.objects.create(estado='cancelada')
        response=self.client.get('/calendario/',{'estado':'cancelada'})
        self.assertEqual(response.context['result_count'],1)

    def test_date_forms_render_and_reject_invalid_ranges(self):
        for url in ['/justificativos/','/autorizaciones/','/rutinas/','/auditoria/']:
            response=self.client.get(url,{'desde':'2026-11-20','hasta':'2026-11-01'})
            self.assertContains(response,'Desde no puede ser posterior a Hasta.')
            self.assertEqual(response.context['result_count'],0)

    def test_document_date_type_category_and_inclusive_end(self):
        from .models import Justificativo, Evaluacion, Autorizacion
        today = timezone.localdate()
        session = ClaseEntrenamiento.objects.create(fecha=today-timedelta(days=8))
        ev = Evaluacion.objects.create(jugador=self.player, clase=session, asistencia='A')
        doc = Justificativo.objects.create(evaluacion=ev, archivo='ficticio.pdf', motivo='Prueba')
        params = {'desde':str(today), 'hasta':str(today), 'categoria':self.player.categoria}
        response=self.client.get('/justificativos/',params)
        self.assertEqual(response.context['result_count'],1)
        response=self.client.get('/justificativos/',dict(params,fecha_tipo='clase'))
        self.assertEqual(response.context['result_count'],0)
        Autorizacion.objects.create(jugador=self.player, fecha=today, archivo='ficticio.pdf', apoderado='Prueba', responsable='Prueba')
        self.assertEqual(self.client.get('/autorizaciones/',params).context['result_count'],1)
