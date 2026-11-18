# Validación de Resultados, Análisis de Discrepancias y Recomendaciones de Mejora Continua

Sistema de Seguimiento Deportivo — **CD Huachipato (Hockey en Patines)** · Evaluación 3 (TIHI43).

Este documento formaliza la cobertura de los criterios **3.1.5.9**, **3.1.5.10**, **3.1.5.11**, **3.1.6.12** y **3.1.6.13** de la rúbrica de evaluación, integrando:
1. Validación cuantitativa de las **60 pruebas automatizadas** (`verificar_proyecto.py`), los **15 casos funcionales/seguridad** ([`docs/plan-pruebas.md`](plan-pruebas.md)), las **9 pruebas de control de acceso** ([`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md)) y los **5 escenarios de estrés y borde** (`scripts/prueba_estres.py`).
2. Comparación exhaustiva entre **Resultados Esperados vs. Resultados Obtenidos**, con identificación precisa de las **7 discrepancias reales (`D-01` a `D-07`)** detectadas durante el ciclo de pruebas e integración, análisis de causa raíz y corrección aplicada.
3. **Recomendaciones técnicas de mejora continua (`REC-01` a `REC-07`)** directamente trazadas a cada discrepancia observada.

---

## 1. Síntesis de Validación Cuantitativa (Criterios 3.1.5.9, 3.1.5.10 y 3.1.5.11)

| Batería de pruebas | Instrumento reproducible | Casos / Métrica meta | Resultado obtenido | Estado |
|---|---|---|---|---|
| **Pruebas unitarias e integración aisladas** | `PROBAR.cmd` / `verificar_proyecto.py` | 100 % de métodos `OK` (`60` tests), `0` errores `check`, `0` migraciones pendientes | **60/60 tests aprobados** en `31.44 s` ([`ejecucion-2026-11-18-control-acceso.txt`](evidencias/ejecucion-2026-11-18-control-acceso.txt)) | **VALIDADO** |
| **Matriz de 15 casos críticos (Seguridad + Negocio)** | [`docs/plan-pruebas.md`](plan-pruebas.md) | `4` casos de corte (`CP-S1`..`CP-S4`) + `11` casos funcionales (`CP-F1`..`CP-F11`) | **15/15 casos aprobados** en entorno local y en despliegue público Vercel (`https://huachipato-cdh.vercel.app/`) | **VALIDADO** |
| **Suite específica de Control de Acceso (RBAC / Anti-IDOR / CSRF)** | `seguimiento/test_access_control.py` ([`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md)) | `9` escenarios sobre las `37` rutas protegidas y `6` niveles de actor | **9/9 aprobados** (`0` accesos indebidos, `0` fugas horizontales entre deportistas) | **VALIDADO** |
| **Verificación de rendimiento SLA (< 1 s) y Seguridad HTTP (H5)** | `scripts/verificar_h5.py` | Latencia `< 1000 ms` por vista, `HttpOnly`, `SameSite=Lax`, `X-Frame-Options=DENY`, `nosniff`, `0` `<style>` inline | Promedios entre `0.4 ms` y `134.79 ms` (`10/10` bajo SLA); cabeceras y aislamiento Ley 19.628 verificados | **VALIDADO** |
| **Pruebas de estrés, volumen y borde (`PE-01` a `PE-05`)** | `scripts/prueba_estres.py` ([`ejecucion-2026-11-18-estres.txt`](evidencias/ejecucion-2026-11-18-estres.txt)) | `150` jugadores, `1.000+` evaluaciones, ráfaga de `200` escrituras JSON, `10` PDFs masivos y `100` cargas corruptas sin `HTTP 500` | **`332.3 ops/s`** en escritura (`p95 = 3.58 ms`), vistas con 150 jugadores en `p95 <= 24.84 ms`, PDFs en `p95 = 372.04 ms`, `0` errores `500` | **VALIDADO** |

### Detalle de resultados de la Prueba de Estrés y Borde (`scripts/prueba_estres.py`)

| ID | Escenario de estrés / borde | Volumen inyectado | Esperado (SLA / Criterio) | Obtenido (Promedio / p95 / Máx) | Conclusión |
|---|---|---|---|---|---|
| **PE-01** | Carga masiva inicial en base de datos | `150` jugadores, `24` sesiones, `1.000` evaluaciones, `60` equipos, `60` préstamos, `150` rutinas | Inserción íntegra sin bloqueos ni violaciones de restricción (`< 1000 ms`) | Completado en **`63.65 ms`** (`100 %` integridad referencial) | **APROBADO** |
| **PE-02** | Ráfaga intensiva de guardado en pista (`POST /evaluaciones/guardar/`) | `200` peticiones JSON consecutivas de calificación y asistencia | `100 % HTTP 200`, `p95 < 1000 ms`, `0` pérdidas de auditoría | `200/200 HTTP 200` · **`332.3 ops/s`** · prom `3.01 ms` · `p95 = 3.58 ms` · `p99 = 4.27 ms` · máx `45.19 ms` | **APROBADO** |
| **PE-03** | Consultas concurrentes de alto volumen (`GET` en 8 módulos + CSV) | `15` iteraciones por módulo con `150` jugadores y `1.200` evaluaciones | `HTTP 200` y `p95 < 1000 ms` en todos los módulos | Promedios `6.16 ms`–`17.11 ms` · `p95` entre **`7.30 ms` y `24.84 ms`** · máx `40.86 ms` | **APROBADO** |
| **PE-04** | Generación masiva de reportes PDF (`ReportLab`) | `10` reportes mensuales PDF sobre `50` deportistas Sub-15 | PDF válido (`%PDF`), `0` fugas de `observacion_privada`, `p95 < 1000 ms` | `10/10` válidos · prom **`327.35 ms`** · `p95 = 372.04 ms` · máx `411.46 ms` · `0` fugas | **APROBADO** |
| **PE-05** | Bombardeo de entradas malformadas, bordes y ataques RBAC | `100` solicitudes (`JSON` truncado, nota `15`, `?sesion=invalido'--`, acceso alumno a `/equipo-tecnico/`) | `0` errores `HTTP 500`; rechazo controlado (`400`/`403`) en `< 50 ms` | `100/100` rechazadas limpiamente (`0` errores `500`) · prom **`1.30 ms`** · `p95 = 1.62 ms` | **APROBADO** |

---

## 2. Comparación Resultados Esperados vs. Obtenidos y Análisis de Discrepancias (Criterio 3.1.6.12)

Durante la ejecución iterativa del protocolo de pruebas (locales y en el entorno productivo Vercel + Supabase) se identificaron **7 discrepancias técnicas reales (`D-01` a `D-07`)** entre el comportamiento inicialmente esperado y el comportamiento observado. Todas fueron analizadas hasta su causa raíz, corregidas en código y verificadas mediante pruebas de regresión.

| ID | Caso / Módulo afectado | Resultado Esperado | Resultado Obtenido Inicialmente (Discrepancia) | Análisis de Causa Raíz | Corrección Implementada y Estado Final |
|---|---|---|---|---|---|
| **D-01** | **CP-S4** · Evaluación en pista (`/pista/?sesion=...`) | Cualquier valor inválido en `?sesion=` debe rechazarse con `HTTP 400` sin llegar al motor de base de datos. | Al enviar `?sesion=abc`, comillas o enteros mayores a 64 bits (`999...`), la conversión directa o consulta al ORM arrojaba excepción no controlada (`ValueError` / `OverflowError` → `HTTP 500`). | `request.GET['sesion']` se pasaba directo a `get_object_or_404(ClaseEntrenamiento, pk=...)` sin validar antes formato ASCII decimal ni límite `BIGINT` (`<= 9223372036854775807`). | Se añadió guarda explícita en `pilot_views.pista` y `home` (commit `264873a`) y prueba `test_invalid_session_identifiers`. **Resuelto (`HTTP 400` controlado).** |
| **D-02** | **CP-S4 / CP-F3** · Calendario y repetición semanal (`/calendario/`, `/clases/nueva/`) | Fechas fuera de rango (`0001-01-01`, `9999-12-31`) o series de 12 semanas al borde del año `9999` deben rechazarse atómicamente sin crear registros parciales. | `anchor - timedelta(days=...)` en año `0001` o sumar `11` semanas en diciembre `9998`/`9999` provocaba `OverflowError: date value out of range` y podía dejar clases creadas a medias antes del fallo. | `datetime.date` en Python admite años `1..9999`, pero al calcular grillas mensuales o sumar semanas (`timedelta(weeks=i)`) se desbordaba el límite sin validación previa en `SessionForm.clean()`. | Se restringió el rango admitido a años `2..9998` en `schedule` y en `SessionForm.clean()` (calculando la fecha final antes de insertar en `transaction.atomic()`, commit `5537b0a`). **Resuelto (`0` series parciales).** |
| **D-03** | **CP-S3** · Revisión de justificativos (`/justificativos/<id>/revisar/`) | Un justificativo ya cerrado (`aprobado` o `rechazado`) debe ser inmutable frente a reenvíos `POST` posteriores. | Un segundo `POST` sobre el mismo ID permitía sobrescribir el estado y la `observacion_revision`, alterando la trazabilidad histórica de la asistencia. | El endpoint verificaba el método `POST` y el rol `@coach_titular`, pero no comprobaba que `doc.estado == 'pendiente'` dentro de un bloqueo transaccional antes de actualizar. | Se bloqueó toda modificación cuando `doc.estado != 'pendiente'`, cubierto por `test_reviewed_document_cannot_be_reopened_or_reversed` (commit `50cf33f`). **Resuelto (registro cerrado inmutable).** |
| **D-04** | **3.1.3.5 / 3.1.4.7** · Configuración de `SECRET_KEY` en producción (`miproyecto/settings.py`) | En Vercel o con `DEBUG=False`, el sistema debe rechazar el arranque si `SECRET_KEY` está ausente, es corta (`< 50` caracteres), repetitiva o usa el prefijo de desarrollo `django-insecure-`. | Si se omitía `SECRET_KEY` en variables de entorno, Django caía silenciosamente en la clave de respaldo de desarrollo, incumpliendo el control `security.W009`. | `os.environ.get('SECRET_KEY', 'django-insecure-...')` aplicaba el valor por defecto tanto en desarrollo local como en producción. | Se implementó validación de arranque en `settings.py` (`ImproperlyConfigured` si `IS_VERCEL or not DEBUG` con clave débil), guía [`SEGURIDAD_SECRET_KEY.md`](../SEGURIDAD_SECRET_KEY.md), rotación en Vercel y 5 pruebas en `test_secret_key.py` (commit `e86479e`). **Resuelto.** |
| **D-05** | **CP-F8 / CP-F9** · Carga de archivos en Vercel Serverless (`Justificativo` y `Autorizacion`) | La carga de documentos PDF/JPG debe validarse con mensaje claro en la interfaz sin ser cortada abruptamente por el proxy de infraestructura. | El límite inicial de validación en Django estaba en `5 MB`, pero las funciones Serverless de Vercel rechazan cuerpos HTTP mayores a `4,5 MB` (`413 FUNCTION_PAYLOAD_TOO_LARGE`) antes de llegar a Django. | Desajuste entre el límite de aplicación (`5 MB`) y la cota física del runtime Serverless de Vercel (`4,5 MB`). | Se ajustó `MAX_UPLOAD_SIZE = 4 * 1024 * 1024` (`4 MB`), se agregó cálculo de huella `SHA-256` (`hash_documento`) y limpieza de archivos reemplazados en Storage (commit `ec17a8c`, validado en `Block3Tests`). **Resuelto.** |
| **D-06** | **3.1.4.7 / 3.1.5.10** · Aislamiento entre entorno de pruebas local y Supabase producción | Ejecutar `manage.py test` o `runserver` en el PC de desarrollo nunca debe tocar la base PostgreSQL ni el bucket `huachipato-media` de producción. | Con `.env` configurado hacia Supabase, `STORAGES['default']` seguía apuntando a `SupabaseStorage` durante `manage.py test`, y en Windows Application Control los binarios C de `psycopg` o el pooler generaban errores de conexión local. | `STORAGES` evaluaba solo `SUPABASE_URL` sin excluir `TESTING`, y faltaba un modo explícito de aislamiento local y un ejecutor independiente de `.env`. | Se aisló `USE_SUPABASE_STORAGE = bool(not TESTING and ...)`, se añadió `LOCAL_SQLITE=1` en `INICIAR.cmd`, fallback `django-pg8000` en Windows y el ejecutor hermético `PROBAR.cmd` + `miproyecto/test_settings.py` (commits `1119572`, `b955840`). **Resuelto.** |
| **D-07** | **CP-F4 / Calendario** · Eliminación de sesiones de entrenamiento vs. preservación histórica | Permitir limpiar sesiones futuras agendadas por error sin abrir una brecha que borre clases ya impartidas o con evaluaciones registradas. | Inicialmente no existía acción de borrado para clases programadas por error, o bien existía el riesgo de eliminar en cascada (`CASCADE`) evaluaciones históricas si se habilitaba un borrado genérico. | `Evaluacion.clase` tiene `on_delete=models.CASCADE`; un borrado sin guarda de estado eliminaría notas históricas de los deportistas. | Se implementó `session_delete` (`/clases/<id>/eliminar/`) restringido estrictamente a `estado == 'programada'` y `not evaluacion_set.exists()`, exigiendo cambio de estado a `cancelada` para sesiones ya evaluadas (commit `081e6e4`). **Resuelto.** |

---

## 3. Recomendaciones Técnicas Basadas en la Comparación de Resultados (Criterio 3.1.6.13)

A partir del análisis de las discrepancias anteriores y de las métricas obtenidas en las pruebas de estrés (`scripts/prueba_estres.py`), se formulan **7 recomendaciones concretas, priorizadas y accionables** para la evolución y mejora continua de la plataforma del Club Deportivo Huachipato:

### REC-01 (Origen: D-05) — Carga directa a Supabase Storage mediante *Presigned URLs*
- **Problema abordado:** El límite de `4 MB` en subidas que pasan a través de la función Serverless de Vercel.
- **Recomendación técnica:** Implementar URLs firmadas de subida temporal (*Signed Upload URLs* de Supabase Storage con expiración de `60 s` generadas por Django) para que el navegador envíe certificados médicos o PDFs de alta resolución (hasta `15–20 MB`) directamente al bucket privado `huachipato-media`, registrando luego en Django únicamente la confirmación y el hash `SHA-256`.

### REC-02 (Origen: PE-02 y D-06) — Migración a *Transaction Pooler* (`:6543`) e índices compuestos en PostgreSQL
- **Problema abordado:** En escenarios de alta concurrencia móvil en cancha (`332.3 ops/s` medidos en `PE-02`), las funciones Serverless abren múltiples conexiones efímeras (`conn_max_age=0`).
- **Recomendación técnica:**
  1. Configurar `DATABASE_URL` en Vercel apuntando al puerto `:6543` (*Supavisor Transaction Pooler*), que ya está soportado en `miproyecto/settings.py` (`DISABLE_SERVER_SIDE_CURSORS = True`).
  2. Incorporar índices compuestos (`models.Index(fields=['estado', 'fecha'])` en `ClaseEntrenamiento` y `models.Index(fields=['estado', '-creado'])` en `Justificativo` y `Autorizacion`) cuando el historial supere las `10.000` evaluaciones anuales.

### REC-03 (Origen: PE-04) — Caché de reportes PDF mensuales vinculada a última modificación
- **Problema abordado:** La generación de PDF con `ReportLab` es la operación más intensiva en CPU (`prom = 327.35 ms`, `máx = 411.46 ms` para 50 jugadores en `PE-04`), aunque cumple holgadamente el SLA de `< 1000 ms`.
- **Recomendación técnica:** Almacenar en caché (o en una carpeta privada `reportes_cache/` de Supabase Storage indexada por `(mes, categoria, jugador_id, max_evaluacion_id)`) los PDFs de meses ya cerrados, reduciendo la latencia de descargas repetidas de `~330 ms` a `< 25 ms`.

### REC-04 (Origen: D-06 y 3.1.5.10) — Pipeline CI/CD en GitHub Actions para ejecución automática en cada Pull Request
- **Problema abordado:** Actualmente `PROBAR.cmd` (`60` tests), `scripts/verificar_h5.py` y `scripts/prueba_estres.py` se ejecutan localmente antes de integrar cambios.
- **Recomendación técnica:** Agregar un workflow `.github/workflows/ci.yml` que ejecute automáticamente `python verificar_proyecto.py` y `python scripts/verificar_h5.py` en cada `push` y `pull_request` hacia `main`, bloqueando fusiones en GitHub si alguna de las 60 pruebas o el chequeo de migraciones falla.

### REC-05 (Origen: D-01, D-02 y D-03) — Capa transversal de limitación de tasa (*Rate Limiting*) en autenticación y endpoints JSON
- **Problema abordado:** Aunque las entradas malformadas y ataques RBAC se rechazan en `1.30 ms` sin errores `500` (`PE-05`), un atacante externo podría automatizar intentos de fuerza bruta contra `/accounts/login/`.
- **Recomendación técnica:** Incorporar control de intentos fallidos de inicio de sesión (`django-axes` o contador por IP/RUT en caché con bloqueo temporal de `5 min` tras `5` intentos fallidos) y límite de tasa en `/evaluaciones/guardar/`.

### REC-06 (Origen: D-04) — Política de rotación semestral de credenciales y secreto de sesión
- **Problema abordado:** Protección continua de `SECRET_KEY`, `DATABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`.
- **Recomendación técnica:** Establecer al cierre de cada semestre deportivo una rotación programada de `SECRET_KEY` en Vercel y de la clave `sb_secret_...` en Supabase, utilizando el validador automático de arranque (`test_secret_key.py`) para verificar la fortaleza de la nueva clave antes del despliegue.

### REC-07 (Origen: Operación en cancha / Offline) — Evolución de cola `localStorage` a *Service Worker* con *Background Sync*
- **Problema abordado:** La cola offline actual en `seguimiento/static/seguimiento/js/pista.js` resguarda en `localStorage` las evaluaciones cuando cae la señal en el gimnasio y las reenvía al reconectar con la pestaña abierta.
- **Recomendación técnica:** Complementar el manifiesto PWA actual (`/manifest.webmanifest`) con un *Service Worker* que implemente la API `Background Sync`, permitiendo sincronizar la cola de evaluaciones automáticamente en segundo plano incluso si el entrenador bloquea el teléfono antes de recuperar cobertura.
