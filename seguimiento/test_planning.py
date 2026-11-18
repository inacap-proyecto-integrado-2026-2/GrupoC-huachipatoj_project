import json
import tempfile
from datetime import timedelta
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from pypdf import PdfReader
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Autorizacion
from .report_pdf import report_data, mean

class PlanningTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('entrenador',is_staff=True)
        self.student=User.objects.create_user('DEMO-TEST')
        self.player=Jugador.objects.create(rut='DEMO-TEST',nombre_completo='Alumno prueba',categoria='S15',fecha_nacimiento='2012-01-01',contacto_emergencia='DEMO')
        self.client.force_login(self.user)
        self.today=timezone.localdate()
    def session(self,**kwargs):
        values=dict(fecha=self.today,hora='18:00',categoria='S15',estado='realizada',objetivo='Pase')
        values.update(kwargs);return ClaseEntrenamiento.objects.create(**values)
    def evaluation(self,s,**kwargs):
        values=dict(jugador=self.player,clase=s,categoria_registrada='S15',asistencia='P',nota_frenado=8,nota_pase=0,nota_tiro=6)
        values.update(kwargs);return Evaluacion.objects.create(**values)
    def test_new_pages_and_invalid_filters(self):
        for url in ['/calendario/','/calendario/?vista=semana','/calendario/?fecha=mal','/calendario/?vista=lista','/clases/nueva/','/reportes/','/autorizaciones/','/autorizaciones/nueva/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
        self.assertContains(self.client.get('/reportes/?mes=2026-10'),'Selecciona un jugador o una categoría')
    def test_create_future_and_block_evaluation(self):
        future=self.today+timedelta(days=4)
        data=dict(fecha=str(future),hora='19:00',categoria='S15',profesor='Prueba',objetivo='Control',estado='programada')
        self.assertEqual(self.client.post('/clases/nueva/',data).status_code,302)
        s=ClaseEntrenamiento.objects.get()
        self.assertEqual(s.fecha,future)
        payload=dict(jugador=self.player.pk,sesion=s.pk,asistencia='P',nota_frenado=8,nota_pase=8,nota_tiro=8)
        self.assertEqual(self.client.post('/evaluaciones/guardar/',json.dumps(payload),content_type='application/json').status_code,409)
        data['estado']='realizada'
        self.assertContains(self.client.post(f'/clases/{s.pk}/editar/',data),'Una clase futura')
    def test_cancel_preserves_history_and_excludes_average(self):
        s=self.session();e=self.evaluation(s)
        data=dict(fecha=str(s.fecha),hora='18:00',categoria='S15',profesor='Prueba',objetivo='Control',estado='cancelada')
        self.assertEqual(self.client.post(f'/clases/{s.pk}/editar/',data).status_code,302)
        e.refresh_from_db();self.assertEqual(e.nota_frenado,8)
        rows,sessions,valid=report_data(self.today,self.player)
        self.assertFalse(valid);self.assertIsNone(mean(rows,'nota_frenado'))
        data['fecha']=str(self.today-timedelta(days=1))
        self.assertContains(self.client.post(f'/clases/{s.pk}/editar/',data),'Conserva su fecha')
    def test_private_observation_not_in_student_or_pdf(self):
        e=self.evaluation(self.session())
        self.assertEqual(self.client.post(f'/evaluaciones/{e.pk}/observacion/',{'observacion_privada':'PRIVADO_NO_EXPORTAR'}).status_code,302)
        self.assertContains(self.client.get(f'/jugadores/{self.player.pk}/'),'PRIVADO_NO_EXPORTAR')
        response=self.client.get('/reportes/',{'mes':self.today.strftime('%Y-%m'),'jugador':self.player.pk})
        self.assertEqual(response['Content-Type'],'application/pdf')
        text=' '.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
        self.assertNotIn('PRIVADO_NO_EXPORTAR',text)
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get('/'),'PRIVADO_NO_EXPORTAR')
        for url in ['/reportes/','/autorizaciones/','/calendario/',f'/evaluaciones/{e.pk}/observacion/']:
            self.assertEqual(self.client.get(url).status_code,403)
    def test_average_and_month_category_filter(self):
        self.evaluation(self.session())
        self.evaluation(self.session(),asistencia='A',nota_frenado=10)
        self.evaluation(self.session(estado='cancelada'),nota_frenado=10)
        self.evaluation(self.session(fecha=self.today.replace(day=1)-timedelta(days=1)),nota_frenado=2)
        rows,sessions,valid=report_data(self.today,category='S15')
        self.assertEqual(mean(valid,'nota_frenado'),8)
        self.assertIsNone(mean(valid,'nota_pase'))
        self.assertFalse(report_data(self.today,category='ESC')[0])
    def test_authorization_upload_edit_and_private_download(self):
        with tempfile.TemporaryDirectory() as tmp,override_settings(MEDIA_ROOT=tmp):
            data=dict(jugador=self.player.pk,apoderado='Prueba',fecha=str(self.today),responsable='Encargado',estado='pendiente')
            bad=SimpleUploadedFile('test.pdf',b'invalido')
            self.client.post('/autorizaciones/nueva/',{**data,'archivo':bad});self.assertEqual(Autorizacion.objects.count(),0)
            file=SimpleUploadedFile('test.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf')
            self.assertEqual(self.client.post('/autorizaciones/nueva/',{**data,'archivo':file}).status_code,302)
            obj=Autorizacion.objects.get();data['estado']='revocada'
            self.assertEqual(self.client.post(f'/autorizaciones/{obj.pk}/editar/',data).status_code,302)
            obj.refresh_from_db();self.assertEqual(obj.estado,'revocada')
            response=self.client.get(f'/autorizaciones/{obj.pk}/archivo/');self.assertEqual(response.status_code,200);response.close()
            self.client.force_login(self.student)
            self.assertEqual(self.client.get(f'/autorizaciones/{obj.pk}/archivo/').status_code,403)
    def test_score_preserves_comment_and_snapshot(self):
        s=self.session();e=self.evaluation(s,observacion_privada='Privada')
        data=dict(jugador=self.player.pk,sesion=s.pk,asistencia='P',nota_frenado=9,nota_pase=7,nota_tiro=8)
        self.client.post('/evaluaciones/guardar/',json.dumps(data),content_type='application/json')
        e.refresh_from_db();self.assertEqual(e.observacion_privada,'Privada');self.assertEqual(e.categoria_registrada,'S15')

    def test_edit_form_preserves_existing_values(self):
        s=self.session(fecha=self.today-timedelta(days=3),profesor='Entrenador original')
        response=self.client.get(f'/clases/{s.pk}/editar/')
        form=response.context['form']
        self.assertEqual(form['estado'].value(),'realizada')
        self.assertEqual(form['fecha'].value(),s.fecha)
        self.assertEqual(form['profesor'].value(),'Entrenador original')

    def test_delete_scheduled_session_and_protect_realized_or_evaluated(self):
        scheduled = self.session(estado='programada', fecha=self.today + timedelta(days=2))
        res_get = self.client.get(f'/clases/{scheduled.pk}/editar/')
        self.assertContains(res_get, f'/clases/{scheduled.pk}/eliminar/')
        res_del_page = self.client.get(f'/clases/{scheduled.pk}/eliminar/')
        self.assertEqual(res_del_page.status_code, 200)
        res_delete = self.client.post(f'/clases/{scheduled.pk}/eliminar/')
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(ClaseEntrenamiento.objects.filter(pk=scheduled.pk).exists())

        realized = self.session(estado='realizada', fecha=self.today)
        res_realized = self.client.post(f'/clases/{realized.pk}/eliminar/')
        self.assertEqual(res_realized.status_code, 302)
        self.assertTrue(ClaseEntrenamiento.objects.filter(pk=realized.pk).exists())

        scheduled_eval = self.session(estado='programada', fecha=self.today + timedelta(days=1))
        self.evaluation(scheduled_eval)
        res_eval = self.client.post(f'/clases/{scheduled_eval.pk}/eliminar/')
        self.assertEqual(res_eval.status_code, 302)
        self.assertTrue(ClaseEntrenamiento.objects.filter(pk=scheduled_eval.pk).exists())

        scheduled_student = self.session(estado='programada', fecha=self.today + timedelta(days=3))
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(f'/clases/{scheduled_student.pk}/eliminar/').status_code, 403)
