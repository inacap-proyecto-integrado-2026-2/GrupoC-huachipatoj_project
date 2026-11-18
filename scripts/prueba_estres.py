r"""
Prueba formal de estrés, volumen y borde — CD Huachipato (Criterio 3.1.5.9 / 3.1.5.10).

Ejecución aislada en memoria (no toca db.sqlite3 ni Supabase):
    .\.venv\Scripts\python.exe scripts\prueba_estres.py
"""

import io
import json
import os
import statistics
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

_tmp_media = tempfile.TemporaryDirectory()
os.environ['LOCAL_SQLITE'] = '1'
os.environ['HUACHIPATO_TEST_MEDIA'] = _tmp_media.name
os.environ.pop('VERCEL', None)
os.environ.pop('VERCEL_ENV', None)
os.environ['DJANGO_SETTINGS_MODULE'] = 'miproyecto.test_settings'

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import (  # noqa: E402
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)
from django.utils import timezone  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from seguimiento.models import (  # noqa: E402
    Auditoria,
    ClaseEntrenamiento,
    Equipo,
    Evaluacion,
    Jugador,
    Prestamo,
    Rutina,
)
from seguimiento.roles import ROL_ADMIN, ROL_ASISTENTE, ROL_ENTRENADOR, assign_staff_role  # noqa: E402


def calcular_rut_dv(numero: int) -> str:
    factores = [2, 3, 4, 5, 6, 7]
    suma = 0
    for idx, digito in enumerate(reversed(str(numero))):
        suma += int(digito) * factores[idx % len(factores)]
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def formatear_rut(numero: int) -> str:
    dv = calcular_rut_dv(numero)
    s = f'{numero:,}'.replace(',', '.')
    return f'{s}-{dv}'


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def summarize_times(times_ms):
    s = sorted(times_ms)
    return {
        'n': len(s),
        'avg_ms': round(statistics.mean(s), 2),
        'p50_ms': round(percentile(s, 50), 2),
        'p95_ms': round(percentile(s, 95), 2),
        'p99_ms': round(percentile(s, 99), 2),
        'max_ms': round(max(s), 2),
    }


def run_stress_suite():
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')

    setup_test_environment()
    old_config = setup_databases(verbosity=0, interactive=False)
    try:
        today = timezone.localdate()
        print('======================================================================')
        print('PRUEBA DE ESTRÉS, VOLUMEN Y BORDE — SISTEMA DEPORTIVO CD HUACHIPATO')
        print('======================================================================')
        print('Entorno: SQLite en memoria aislado (miproyecto.test_settings)')

        # ------------------------------------------------------------------
        # PE-01: Carga masiva de datos (150 deportistas, 24 sesiones, 1200 evaluaciones)
        # ------------------------------------------------------------------
        print('\n>>> PE-01: Carga masiva de plantilla, sesiones, evaluaciones e inventario')
        t0 = time.perf_counter()

        admin = User.objects.create_user('stress_admin', is_staff=True)
        assign_staff_role(admin, ROL_ADMIN)
        coach = User.objects.create_user('stress_coach', is_staff=True)
        assign_staff_role(coach, ROL_ENTRENADOR)
        assistant = User.objects.create_user('stress_asistente', is_staff=True)
        assign_staff_role(assistant, ROL_ASISTENTE)

        categorias = ['ESC', 'S15', 'ADU']
        players = [
            Jugador(
                rut=formatear_rut(15000000 + i),
                nombre_completo=f'Deportista Estrés {i + 1:03d}',
                categoria=categorias[i % 3],
                fecha_nacimiento=f'{2002 + (i % 15)}-05-{(i % 28) + 1:02d}',
                contacto_emergencia=f'98765{i:04d}',
            )
            for i in range(150)
        ]
        Jugador.objects.bulk_create(players)
        players = list(Jugador.objects.order_by('id'))

        sessions = []
        for s_idx in range(24):
            sessions.append(
                ClaseEntrenamiento(
                    fecha=today - timedelta(days=24 - s_idx),
                    hora='18:00',
                    categoria=categorias[s_idx % 3],
                    profesor='Waldo Rivas',
                    objetivo=f'Sesión de carga #{s_idx + 1}',
                    estado='realizada',
                )
            )
        ClaseEntrenamiento.objects.bulk_create(sessions)
        sessions = list(ClaseEntrenamiento.objects.order_by('id'))

        evals_bulk = []
        for s_idx, sess in enumerate(sessions[:20]):
            cat_players = [p for p in players if p.categoria == sess.categoria]
            for p_idx, p in enumerate(cat_players):
                att = 'P' if (p_idx + s_idx) % 7 != 0 else 'A'
                score = 6 + ((p_idx + s_idx) % 5) if att == 'P' else 0
                evals_bulk.append(
                    Evaluacion(
                        jugador=p,
                        clase=sess,
                        categoria_registrada=sess.categoria,
                        asistencia=att,
                        nota_frenado=score,
                        nota_pase=score,
                        nota_tiro=max(1, score - 1) if att == 'P' else 0,
                        observacion_privada='[CONFIDENCIAL_ESTRES] Control técnico.',
                    )
                )
        Evaluacion.objects.bulk_create(evals_bulk)

        equipos_bulk = [
            Equipo(
                codigo=f'CDH-ST-{i + 1:03d}',
                nombre=f'Equipo Estrés {i + 1:03d}',
                estado='bueno' if i % 4 != 0 else 'desgastado',
            )
            for i in range(60)
        ]
        Equipo.objects.bulk_create(equipos_bulk)
        equipos = list(Equipo.objects.order_by('id'))

        prestamos_bulk = [
            Prestamo(equipo=equipos[i], jugador=players[i], devuelto=None if i < 30 else timezone.now())
            for i in range(60)
        ]
        Prestamo.objects.bulk_create(prestamos_bulk)

        rutinas_bulk = [
            Rutina(
                jugador=players[i],
                titulo=f'Rutina intensiva #{i + 1}',
                objetivo='Resistencia y control de bocha',
                ejercicios='Series 4x10 con patín',
                fecha=today + timedelta(days=(i % 7) - 3),
                completada=(i % 2 == 0),
            )
            for i in range(150)
        ]
        Rutina.objects.bulk_create(rutinas_bulk)

        elapsed_seed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        print(
            f'  Semilla completada en {elapsed_seed_ms} ms: '
            f'{Jugador.objects.count()} jugadores, {ClaseEntrenamiento.objects.count()} clases, '
            f'{Evaluacion.objects.count()} evaluaciones, {Equipo.objects.count()} equipos, '
            f'{Rutina.objects.count()} rutinas.'
        )

        # ------------------------------------------------------------------
        # PE-02: Ráfaga de 200 guardados en vivo en pista (POST /evaluaciones/guardar/)
        # ------------------------------------------------------------------
        print('\n>>> PE-02: Ráfaga de 200 escrituras JSON en pista (POST /evaluaciones/guardar/)')
        client = Client()
        client.force_login(coach)
        target_session = sessions[-1]
        session_players = [p for p in players if not target_session.categoria or p.categoria == target_session.categoria]

        burst_times = []
        status_codes = []
        t_burst_start = time.perf_counter()
        for idx in range(200):
            player = session_players[idx % len(session_players)]
            payload = {
                'jugador': player.pk,
                'sesion': target_session.pk,
                'asistencia': 'P' if idx % 10 != 0 else 'T',
                'nota_frenado': 7 + (idx % 4),
                'nota_pase': 6 + (idx % 5),
                'nota_tiro': 8 + (idx % 3),
            }
            t_req = time.perf_counter()
            resp = client.post(
                '/evaluaciones/guardar/',
                data=json.dumps(payload),
                content_type='application/json',
            )
            burst_times.append((time.perf_counter() - t_req) * 1000.0)
            status_codes.append(resp.status_code)
        total_burst_s = time.perf_counter() - t_burst_start
        stats_burst = summarize_times(burst_times)
        ops_sec = round(200 / total_burst_s, 1)
        assert all(code == 200 for code in status_codes), f'Fallos en ráfaga: {set(status_codes)}'
        print(
            f'  200/200 HTTP 200 OK | throughput={ops_sec} ops/s | '
            f'prom={stats_burst["avg_ms"]} ms | p50={stats_burst["p50_ms"]} ms | '
            f'p95={stats_burst["p95_ms"]} ms | p99={stats_burst["p99_ms"]} ms | max={stats_burst["max_ms"]} ms'
        )
        assert stats_burst['p95_ms'] < 1000.0, 'p95 superó el SLA de 1000 ms'

        # ------------------------------------------------------------------
        # PE-03: Consultas de alto volumen en vistas operativas y exportación CSV
        # ------------------------------------------------------------------
        print('\n>>> PE-03: Latencia bajo volumen en vistas principales (15 iteraciones c/u)')
        endpoints = [
            ('GET / (Dashboard con 1.200+ evaluaciones)', '/'),
            ('GET /pista/ (150 deportistas)', f'/pista/?sesion={target_session.pk}'),
            ('GET /jugadores/ (150 deportistas + filtros)', '/jugadores/?categoria=S15'),
            ('GET /jugadores/exportar/ (CSV 150 deportistas)', '/jugadores/exportar/'),
            ('GET /calendario/?vista=mes (24 sesiones)', '/calendario/?vista=mes'),
            ('GET /inventario/ (60 equipos + 60 préstamos)', '/inventario/?disponibilidad=prestado'),
            ('GET /rutinas/ (150 rutinas + filtro vencidas)', '/rutinas/?vencidas=on'),
            ('GET /auditoria/ (200+ registros)', '/auditoria/'),
        ]
        for label, url in endpoints:
            times = []
            for _ in range(15):
                t_req = time.perf_counter()
                r = client.get(url)
                times.append((time.perf_counter() - t_req) * 1000.0)
                assert r.status_code == 200, f'{url} devolvió {r.status_code}'
            st = summarize_times(times)
            print(
                f'  - {label}: HTTP 200 | prom={st["avg_ms"]} ms | '
                f'p95={st["p95_ms"]} ms | max={st["max_ms"]} ms | SLA<1000ms=OK'
            )
            assert st['p95_ms'] < 1000.0, f'{label} excedió SLA en p95'

        # ------------------------------------------------------------------
        # PE-04: Generación repetida de reportes PDF bajo carga (ReportLab)
        # ------------------------------------------------------------------
        print('\n>>> PE-04: Generación de 10 reportes PDF mensuales sobre 50 jugadores S15')
        pdf_times = []
        month_str = today.strftime('%Y-%m')
        for _ in range(10):
            t_req = time.perf_counter()
            r = client.get('/reportes/', {'mes': month_str, 'categoria': 'S15'})
            pdf_times.append((time.perf_counter() - t_req) * 1000.0)
            assert r.status_code == 200 and r['Content-Type'] == 'application/pdf'
            reader = PdfReader(io.BytesIO(r.content))
            assert len(reader.pages) >= 1
            text_pdf = ' '.join(p.extract_text() for p in reader.pages)
            assert 'CONFIDENCIAL_ESTRES' not in text_pdf
        st_pdf = summarize_times(pdf_times)
        print(
            f'  10/10 PDFs válidos (0 fugas privadas) | prom={st_pdf["avg_ms"]} ms | '
            f'p95={st_pdf["p95_ms"]} ms | max={st_pdf["max_ms"]} ms | SLA<1000ms=OK'
        )
        assert st_pdf['p95_ms'] < 1000.0

        # ------------------------------------------------------------------
        # PE-05: Estrés de bordes, cargas malformadas y denegación RBAC (100 intentos)
        # ------------------------------------------------------------------
        print('\n>>> PE-05: Ráfaga de 100 entradas de borde, JSON corrupto y bloqueos RBAC')
        student_user = User.objects.create_user(players[0].rut)
        student_client = Client()
        student_client.force_login(student_user)

        edge_times = []
        for idx in range(25):
            # 1) JSON corrupto
            t_req = time.perf_counter()
            r1 = client.post('/evaluaciones/guardar/', data='{corrupto', content_type='application/json')
            edge_times.append((time.perf_counter() - t_req) * 1000.0)
            assert r1.status_code == 400

            # 2) Nota fuera de rango (15)
            t_req = time.perf_counter()
            r2 = client.post(
                '/evaluaciones/guardar/',
                data=json.dumps({'jugador': players[0].pk, 'sesion': target_session.pk, 'asistencia': 'P', 'nota_frenado': 15}),
                content_type='application/json',
            )
            edge_times.append((time.perf_counter() - t_req) * 1000.0)
            assert r2.status_code == 400

            # 3) Identificador de sesión malformado en pista
            t_req = time.perf_counter()
            r3 = client.get('/pista/', {'sesion': f"invalido_{idx}'--"})
            edge_times.append((time.perf_counter() - t_req) * 1000.0)
            assert r3.status_code == 400

            # 4) Intento de acceso no autorizado de alumno a ruta administrativa
            t_req = time.perf_counter()
            r4 = student_client.get('/equipo-tecnico/')
            edge_times.append((time.perf_counter() - t_req) * 1000.0)
            assert r4.status_code == 403

        st_edge = summarize_times(edge_times)
        print(
            f'  100/100 solicitudes rechazadas limpiamente (0 errores HTTP 500) | '
            f'prom={st_edge["avg_ms"]} ms | p95={st_edge["p95_ms"]} ms | max={st_edge["max_ms"]} ms'
        )
        print(f'  Total registros de auditoría generados sin bloqueo: {Auditoria.objects.count()}')
        print('\nRESULTADO FINAL: PRUEBAS DE ESTRÉS Y BORDE SUPERADAS (5/5 ESCENARIOS OK)')
    finally:
        teardown_databases(old_config, verbosity=0)
        teardown_test_environment()
        _tmp_media.cleanup()


if __name__ == '__main__':
    run_stress_suite()
