"""
Verificación automatizada H5 — Rendimiento (<1 s), Seguridad HTTP y Matriz RBAC.

Ejecución segura sin alterar la base local ni Supabase:
    python scripts/verificar_h5.py
Opcional (solo lectura GET contra despliegue público):
    python scripts/verificar_h5.py --url https://tu-app.vercel.app
"""

import argparse
import io
import json
import logging
import os
import statistics
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['LOCAL_SQLITE'] = '1'
os.environ.pop('VERCEL', None)
os.environ.pop('VERCEL_ENV', None)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miproyecto.settings')

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_databases, setup_test_environment, teardown_databases, teardown_test_environment  # noqa: E402
from django.utils import timezone  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from seguimiento.models import ClaseEntrenamiento, Equipo, Evaluacion, Jugador, Prestamo, Rutina  # noqa: E402
from seguimiento.roles import ROL_ASISTENTE, assign_staff_role  # noqa: E402


def check_templates_no_inline_style():
    bad = []
    tpl_root = BASE_DIR / 'seguimiento' / 'templates'
    for path in tpl_root.rglob('*.html'):
        text = path.read_text(encoding='utf-8')
        if '<style' in text.lower():
            bad.append(str(path.relative_to(BASE_DIR)))
    return bad


def measure(client, method, url, *, data=None, content_type=None, runs=5):
    times_ms = []
    last_resp = None
    for _ in range(runs):
        t0 = time.perf_counter()
        if method == 'GET':
            last_resp = client.get(url)
        else:
            kwargs = {'data': data}
            if content_type:
                kwargs['content_type'] = content_type
            last_resp = client.post(url, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000.0
        times_ms.append(elapsed)
    return {
        'status': last_resp.status_code,
        'avg_ms': round(statistics.mean(times_ms), 2),
        'max_ms': round(max(times_ms), 2),
        'resp': last_resp,
    }


def run_local_suite():
    print('=== 1. Chequeo estático y de configuración Django ===')
    check_out = io.StringIO()
    call_command('check', stdout=check_out)
    print(f'python manage.py check -> OK ({check_out.getvalue().strip() or "0 issues"})')

    inline_style_files = check_templates_no_inline_style()
    print(f'Plantillas con etiqueta <style>: {len(inline_style_files)} ({inline_style_files})')
    assert not inline_style_files, f'Se detectó <style> inline en: {inline_style_files}'

    with tempfile.TemporaryDirectory() as media_tmp:
        old_media_root = settings.MEDIA_ROOT
        old_allowed_hosts = list(settings.ALLOWED_HOSTS)
        settings.MEDIA_ROOT = Path(media_tmp)
        if 'testserver' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append('testserver')

        setup_test_environment()
        old_config = setup_databases(verbosity=0, interactive=False)
        try:
            today = timezone.localdate()
            admin = User.objects.create_user('h5_admin', password='H5#Password1', is_staff=True, is_superuser=True)
            coach = User.objects.create_user('h5_coach', password='H5#Password1', is_staff=True)
            assistant = User.objects.create_user('h5_asistente', password='H5#Password1', is_staff=True)
            assign_staff_role(assistant, ROL_ASISTENTE)
            student = User.objects.create_user('18.765.432-1', password='H5#Password1')

            players = []
            for idx in range(20):
                num = 18765432 - idx
                rut = '18.765.432-1' if idx == 0 else f'DEMO-H5-{idx:02d}'
                p = Jugador.objects.create(
                    rut=rut,
                    nombre_completo=f'Jugador H5 {idx + 1}',
                    categoria='S15' if idx % 2 == 0 else 'ESC',
                    fecha_nacimiento='2013-05-10',
                    contacto_emergencia=f'999000{idx:03d}',
                )
                players.append(p)

            session = ClaseEntrenamiento.objects.create(
                fecha=today,
                hora='18:30',
                categoria='S15',
                profesor='Waldo Rivas',
                objetivo='Control de bocha y frenado',
                estado='realizada',
            )
            for p in players[:10]:
                Evaluacion.objects.create(
                    jugador=p,
                    clase=session,
                    categoria_registrada=p.categoria,
                    asistencia='P',
                    nota_frenado=8,
                    nota_pase=7,
                    nota_tiro=8,
                    observacion_privada='OBSERVACION_PRIVADA_H5',
                )
            eq = Equipo.objects.create(codigo='H5-PAT-01', nombre='Patines Prueba', estado='bueno')
            Prestamo.objects.create(equipo=eq, jugador=players[0])
            Rutina.objects.create(
                jugador=players[0],
                titulo='Frenado en T',
                objetivo='Estabilidad',
                ejercicios='4 series de 20 metros',
                fecha=today,
            )

            print('\n=== 2. Rendimiento H5 (meta < 1000 ms por operación, 5 repeticiones c/u) ===')
            c_anon = Client()
            c_coach = Client()
            c_coach.force_login(coach)
            c_student = Client()
            c_student.force_login(student)

            benchmarks = [
                ('GET /accounts/login/ (anónimo)', c_anon, 'GET', '/accounts/login/', None, None),
                ('GET /manifest.webmanifest', c_anon, 'GET', '/manifest.webmanifest', None, None),
                ('GET / (Dashboard entrenador)', c_coach, 'GET', '/', None, None),
                ('GET /pista/ (20 jugadores)', c_coach, 'GET', f'/pista/?sesion={session.pk}', None, None),
                (
                    'POST /evaluaciones/guardar/ (JSON)',
                    c_coach,
                    'POST',
                    '/evaluaciones/guardar/',
                    json.dumps({'jugador': players[0].pk, 'sesion': session.pk, 'asistencia': 'P', 'nota_frenado': 9, 'nota_pase': 8, 'nota_tiro': 8}),
                    'application/json',
                ),
                ('GET /calendario/?vista=mes', c_coach, 'GET', '/calendario/?vista=mes', None, None),
                ('GET /jugadores/', c_coach, 'GET', '/jugadores/', None, None),
                ('GET /inventario/', c_coach, 'GET', '/inventario/', None, None),
                ('GET /reportes/ (PDF mensual)', c_coach, 'GET', f'/reportes/?mes={today.strftime("%Y-%m")}&jugador={players[0].pk}', None, None),
                ('GET / (Portal deportista)', c_student, 'GET', '/', None, None),
            ]

            all_under_sla = True
            pdf_resp = None
            for label, cl, method, url, data, ctype in benchmarks:
                res = measure(cl, method, url, data=data, content_type=ctype, runs=5)
                if label.startswith('GET /reportes/'):
                    pdf_resp = res['resp']
                sla_ok = res['max_ms'] < 1000.0 and res['status'] == 200
                if not sla_ok:
                    all_under_sla = False
                print(f"- {label}: HTTP {res['status']} | prom={res['avg_ms']} ms | max={res['max_ms']} ms | SLA<1000ms={'OK' if sla_ok else 'FAIL'}")

            assert all_under_sla, 'Alguna ruta excedió 1000 ms o no devolvió HTTP 200.'

            print('\n=== 3. Seguridad HTTP, Privacidad (Ley 19.628) y Matriz RBAC ===')
            assert c_anon.get('/').status_code == 302
            print('- Anónimo -> GET /: 302 (redirige a login) [OK]')

            c_login = Client()
            logged = c_login.post('/accounts/login/', {'username': 'h5_coach', 'password': 'H5#Password1'})
            assert logged.status_code == 302
            cookie = c_login.cookies.get(settings.SESSION_COOKIE_NAME)
            assert cookie is not None and cookie['httponly'] and str(cookie['samesite']).lower() == 'lax'
            print(f"- Cookie sesión ({settings.SESSION_COOKIE_NAME}): HttpOnly={bool(cookie['httponly'])}, SameSite={cookie['samesite']} [OK]")

            header_resp = c_coach.get('/pista/')
            assert header_resp.headers.get('X-Frame-Options') == 'DENY'
            assert header_resp.headers.get('X-Content-Type-Options') == 'nosniff'
            print(f"- Cabeceras HTTP: X-Frame-Options={header_resp.headers.get('X-Frame-Options')}, X-Content-Type-Options={header_resp.headers.get('X-Content-Type-Options')} [OK]")

            # Privacidad observacion_privada
            st_html = c_student.get('/').content.decode('utf-8')
            assert 'OBSERVACION_PRIVADA_H5' not in st_html
            pdf_text = ' '.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(pdf_resp.content)).pages)
            assert 'OBSERVACION_PRIVADA_H5' not in pdf_text
            csv_resp = c_coach.get(f'/reportes/?mes={today.strftime("%Y-%m")}&jugador={players[0].pk}&formato=csv')
            assert csv_resp.status_code == 200 and 'OBSERVACION_PRIVADA_H5' not in csv_resp.content.decode('utf-8-sig')
            print('- Aislamiento observacion_privada (Portal alumno + PDF + CSV): 0 fugas [OK]')

            # RBAC matriz
            c_asist = Client()
            c_asist.force_login(assistant)
            c_admin = Client()
            c_admin.force_login(admin)

            rbac_checks = [
                ('Alumno -> /pista/', c_student, '/pista/', 403),
                ('Alumno -> /auditoria/', c_student, '/auditoria/', 403),
                ('Alumno -> /equipo-tecnico/', c_student, '/equipo-tecnico/', 403),
                ('Asistente -> /pista/', c_asist, '/pista/', 200),
                ('Asistente -> /justificativos/', c_asist, '/justificativos/', 403),
                ('Asistente -> /autorizaciones/', c_asist, '/autorizaciones/', 403),
                ('Asistente -> /auditoria/', c_asist, '/auditoria/', 403),
                ('Asistente -> /jugadores/exportar/', c_asist, '/jugadores/exportar/', 403),
                ('Asistente -> /equipo-tecnico/', c_asist, '/equipo-tecnico/', 403),
                ('Entrenador -> /justificativos/', c_coach, '/justificativos/', 200),
                ('Entrenador -> /equipo-tecnico/', c_coach, '/equipo-tecnico/', 403),
                ('Administrador -> /equipo-tecnico/', c_admin, '/equipo-tecnico/', 200),
            ]
            for desc, cl, path, expected in rbac_checks:
                req_logger = logging.getLogger('django.request')
                prev_level = req_logger.level
                if expected >= 400:
                    req_logger.setLevel(logging.ERROR)
                try:
                    code = cl.get(path).status_code
                finally:
                    req_logger.setLevel(prev_level)
                assert code == expected, f'{desc} devolvió {code} en lugar de {expected}'
                print(f'- RBAC {desc}: HTTP {code} [OK]')
        finally:
            teardown_databases(old_config, verbosity=0)
            teardown_test_environment()
            settings.MEDIA_ROOT = old_media_root
            settings.ALLOWED_HOSTS = old_allowed_hosts


def check_remote_url(base_url):
    print(f'\n=== 4. Auditoría HTTP externa de solo lectura: {base_url} ===')
    base = base_url.rstrip('/')
    for path in ['/accounts/login/', '/manifest.webmanifest']:
        url = f'{base}{path}'
        t0 = time.perf_counter()
        req = urllib.request.Request(url, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                ms = round((time.perf_counter() - t0) * 1000.0, 2)
                print(f"- {url} -> HTTP {resp.status} en {ms} ms | XFO={resp.headers.get('X-Frame-Options')} | XCTO={resp.headers.get('X-Content-Type-Options')}")
        except urllib.error.URLError as exc:
            print(f'- {url} -> Error de conexión: {exc}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verificación automatizada H5 (Rendimiento y Seguridad).')
    parser.add_argument('--url', help='URL pública opcional de Vercel para auditoría GET de solo lectura.')
    args = parser.parse_args()
    run_local_suite()
    if args.url:
        check_remote_url(args.url)
    print('\nVERIFICACIÓN H5 COMPLETADA CON ÉXITO.')
