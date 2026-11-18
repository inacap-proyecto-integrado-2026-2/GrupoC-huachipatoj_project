# Guion de Exposición (12 min), Pruebas en Vivo del Docente (5 min) y Defensa Técnica — Evaluación 3

**Proyecto:** Sistema de Seguimiento Deportivo — Club Deportivo Huachipato (Hockey en Patines)  
**Integrantes:** Daniel Ignacio Melimán Vergara · Diego Astudillo Fica  
**URL en producción:** <https://huachipato-cdh.vercel.app/>

---

## 0. Checklist de Preparación (5 minutos antes de exponer)

1. **Verificar pestañas abiertas en el navegador:**
   - Pestaña 1: <https://huachipato-cdh.vercel.app/> con sesión iniciada en `demo.admin` (o `demo.entrenador`).
   - Pestaña 2 (Ventana de incógnito): lista en `/accounts/login/` para cambiar rápido a `demo.asistente` o a la cuenta de deportista durante las preguntas del profesor.
   - Pestaña 3: Repositorio GitHub mostrando [`docs/plan-pruebas.md`](plan-pruebas.md), [`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md) y [`docs/validacion-discrepancias-recomendaciones.md`](validacion-discrepancias-recomendaciones.md).
2. **Celular conectado a datos móviles:** con <https://huachipato-cdh.vercel.app/> abierto en `/pista/` para mostrar diseño responsivo táctil.
3. **Verificación rápida de datos en producción para las pruebas de corte:**
   -En `/jugadores/`, verificar que **`Tomás Vera [DEMO]` (`22.222.222-2`)** tenga el distintivo **«Activa»** en columna *Acceso portal* (si dice *Sin cuenta*, pulsar **`+ Crear acceso`** y anotar la clave temporal para el docente).
   - En `/justificativos/`, verificar que exista al menos **1 justificativo en estado `Aprobado`** (cerrado) y **1 en estado `Pendiente`**, para demostrar en vivo la inmutabilidad del registro cerrado (`CP-S3`).

---

## 1. Estructura Estricta de la Exposición (12 minutos totales)

| Bloque | Tiempo | Expositor sugerido | Contenido clave a presentar | Pantalla de apoyo |
|---|---|---|---|---|
| **1. Alcance real del MVP** | `00:00 – 02:00` *(2 min)* | Daniel Melimán | Problema operativo de la rama de Hockey en Patines de CD Huachipato (planillas dispersas, pérdida de señal en cancha, resguardo de certificados médicos y préstamos). Qué cubre el 100 % del MVP en producción y qué quedó fuera de alcance (pagos/fichas médicas clínicas). | Dashboard en vivo (`/`) |
| **2. Demostración en vivo en la URL pública** | `02:00 – 08:00` *(6 min)* | Daniel Melimán y Diego Astudillo | Recorrido de punta a punta en <https://huachipato-cdh.vercel.app/>: Calendario semanal + Evaluación táctil en pista (`1–10` y observación privada) + Justificativos/Autorizaciones (`SHA-256`) + Inventario y filtros combinados + Reporte PDF mensual + Portal privado del deportista. | Navegador en vivo (escritorio + móvil) |
| **3. Arquitectura, seguridad y despliegue** | `08:00 – 10:00` *(2 min)* | Diego Astudillo | Modelo 4+1, Django 5.2 en Vercel Serverless + WhiteNoise + Supabase PostgreSQL 17 (3FN, `PROTECT`, `UniqueConstraint`) + Supabase Storage privado. Regla eliminatoria 3.1.3: RBAC 4 niveles, anti-IDOR, `SECRET_KEY` validada, Ley 19.628. | Diagrama físico / [`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md) |
| **4. Resultados del plan de pruebas, discrepancias y mejoras** | `10:00 – 12:00` *(2 min)* | Daniel Melimán y Diego Astudillo | Ejecución de **60 tests unitarios (`100 % OK`)**, **15 casos (`CP-S1`..`CP-F11`)**, **5 pruebas de estrés (`150` jugadores, `332,3 ops/s`, `p95 = 3,58 ms`)**, análisis de **7 discrepancias reales (`D-01`..`D-07`)** y **7 recomendaciones (`REC-01`..`REC-07`)**. | [`docs/plan-pruebas.md`](plan-pruebas.md) y [`docs/validacion-discrepancias-recomendaciones.md`](validacion-discrepancias-recomendaciones.md) |

---

### Guion hablado minuto a minuto

#### Bloque 1 · Alcance real del MVP (00:00 – 02:00 · 2 min)
- **Qué decir:**
  > «Buenas tardes profesor. Nuestro proyecto resuelve la gestión deportiva y documental de la rama de Hockey en Patines del Club Deportivo Huachipato, validado con el entrenador jefe Waldo Rivas. Antes se trabajaba con planillas sueltas y mensajes de WhatsApp, sin trazabilidad de préstamos de patines/sticks ni resguardo privado de certificados médicos de menores de edad.
  > El MVP desplegado en producción en `huachipato-cdh.vercel.app` cubre el 100 % del flujo operativo: programación de sesiones semanales, evaluación táctil en pista del 1 al 10 con respaldo offline en `localStorage`, observaciones pedagógicas confidenciales, portal privado del deportista con login por RUT Módulo 11, custodia privada de justificativos y autorizaciones en Supabase Storage con huella `SHA-256`, control de inventario con bloqueo de doble préstamo, reportes mensuales en PDF/CSV y administración RBAC de 4 roles. Quedan explícitamente fuera de alcance cobros de mensualidades e historial clínico hospitalario».

#### Bloque 2 · Demostración en vivo en la URL pública (02:00 – 08:00 · 6 min)
1. **Minuto 02:00–03:15 — Calendario y programación semanal (`/calendario/`):**
   - Mostrar las vistas **Mes**, **Semana** y **Listado**, más los filtros combinados por estado y categoría.
   - Abrir una clase en estado **Programada** sin evaluaciones y mostrar el botón **«Eliminar clase»** (explicando que si una clase ya fue realizada o tiene evaluaciones, el sistema bloquea su eliminación y exige cambiar estado a *Cancelada* para preservar el historial y excluirla de promedios).
2. **Minuto 03:15–04:45 — Evaluación en pista y confidencialidad (`/pista/`):**
   - Seleccionar una sesión realizada, filtrar un jugador en tiempo real y tocar una nota del `1` al `10` en **Frenado**, **Pase** o **Tiro** mostrando la confirmación asíncrona **«Guardado»** (`~3 ms` en servidor).
   - Abrir **«Observación privada»**, mostrar la nota interna del entrenador y recalcar que por **Ley 19.628** jamás se expone al deportista ni en el PDF ni en el CSV.
   - Mencionar la cola offline en `localStorage` (`pista.js`) ante cortes de señal en el gimnasio.
3. **Minuto 04:45–06:00 — Documentos privados, Inventario y Filtros combinados (`/justificativos/`, `/inventario/`):**
   - En **Justificativos**, mostrar el filtro combinado por categoría y tipo de fecha (*fecha de carga* vs *fecha de clase*), la huella de integridad **SHA-256** y la descarga autenticada desde el bucket privado `huachipato-media` de Supabase Storage (archivos PDF/JPG validados por firma binaria hasta `4 MB`).
   - En **Inventario**, filtrar por disponibilidad (`Prestado` / `Libre`) y mostrar cómo la restricción parcial `un_prestamo_activo` en PostgreSQL impide prestar un equipo que ya está en uso.
4. **Minuto 06:00–07:00 — Reportes PDF/CSV y Auditoría (`/reportes/`, `/auditoria/`):**
   - Generar en vivo un **Informe PDF mensual** con `ReportLab`, destacando que calcula los promedios reales excluyendo ausencias y clases canceladas, y que oculta las observaciones privadas.
   - Mostrar la bitácora de **Auditoría** con filtro de fechas y trazabilidad de cada acción.
5. **Minuto 07:00–08:00 — Equipo Técnico RBAC y Portal del Deportista (`/equipo-tecnico/` e incógnito):**
   - En **Equipo técnico**, mostrar la gestión de roles (`Administrador`, `Entrenador`, `Asistente`) y la **eliminación segura de cuentas** (que exige escribir el nombre exacto del usuario, protege superusuarios y retira el acceso conservando intacta la ficha deportiva y el historial).
   - En la ventana de incógnito, mostrar la vista del **Deportista** (gráfico interactivo de evolución, próximas sesiones, préstamos activos y cumplimiento de rutinas).

#### Bloque 3 · Arquitectura, seguridad y despliegue (08:00 – 10:00 · 2 min)
- **Qué decir:**
  > «En arquitectura física operamos bajo un esquema cloud desacoplado: Django 5.2 en funciones Serverless de Vercel con WhiteNoise para activos estáticos, conectado por TLS a PostgreSQL 17 en Supabase (región São Paulo, en Tercera Forma Normal con claves foráneas `PROTECT` e índice único condicional para préstamos activos) y almacenamiento privado en Supabase Storage.
  > En seguridad (Criterio 3.1.3), implementamos defensa en profundidad: validación obligatoria de `SECRET_KEY` de al menos 50 caracteres en producción (`SEGURIDAD_SECRET_KEY.md`), cookies `HttpOnly`/`SameSite=Lax`/`Secure`, cabeceras `X-Frame-Options: DENY`, `nosniff` y HSTS, control de acceso RBAC en servidor sobre las 37 rutas protegidas, aislamiento horizontal anti-IDOR entre deportistas, validación de magic bytes `%PDF-` y `FFD8FF` con hash `SHA-256`, y sanitización anti-inyección de fórmulas en exportaciones CSV».

#### Bloque 4 · Plan de pruebas, discrepancias y recomendaciones (10:00 – 12:00 · 2 min)
- **Qué decir:**
  > «El protocolo de pruebas comprende 60 pruebas automatizadas aisladas ejecutables con `PROBAR.cmd` (`100 % OK` en 31 segundos sin tocar credenciales de producción), los 15 casos críticos de negocio y seguridad aprobados en local y en producción (`docs/plan-pruebas.md`), 9 pruebas exhaustivas de control de acceso (`docs/pruebas-control-acceso.md`) y una suite de estrés (`scripts/prueba_estres.py`) con 150 deportistas y 1.000 evaluaciones que alcanzó 332 operaciones por segundo con latencia percentil 95 de 3,58 ms.
  > Además, en `docs/validacion-discrepancias-recomendaciones.md` documentamos las 7 discrepancias reales detectadas durante las pruebas —como el límite de payload de 4,5 MB en Vercel, el desbordamiento de fechas extremas `0001`/`9999`, el parámetro `?sesion=` malformado y la inmutabilidad de justificativos cerrados—, su causa raíz, la corrección aplicada y 7 recomendaciones de mejora continua, tales como subida directa por *Presigned URLs*, *Transaction Pooler* en puerto 6543 y pipeline CI/CD en GitHub Actions».

---

## 2. Protocolo para las 5 Pruebas en Vivo del Docente (5 minutos · Criterio Eliminatorio 3.1.3)

| # | Prueba que pedirá el docente | Paso exacto para ejecutarla en vivo | Resultado que verá el docente |
|---|---|---|---|
| **1** | **Entrar con perfil mínimo e intentar acción prohibida** (`CP-S2`) | Iniciar sesión con `demo.asistente` (o deportista). Escribir directamente en la barra de direcciones `https://huachipato-cdh.vercel.app/equipo-tecnico/` o `/justificativos/` o `/cuentas/2/eliminar/`. | El servidor responde **`403 Forbidden`** (la restricción se aplica en backend mediante `@club_admin` / `@coach_titular`, no solo ocultando botones). |
| **2** | **Intentar editar un registro cerrado** (`CP-S3`) | Con cuenta de `Entrenador` o `Administrador`, ir a `/justificativos/` y ubicar un justificativo ya **`Aprobado`** (o `Rechazado`). Mostrar que ya está cerrado e intentar reenviar revisión. | En interfaz aparece cerrado con el nombre del revisor; y en servidor (`document_review`), si `doc.estado != 'pendiente'` rechaza cualquier cambio conservando estado, observación y asistencia `J`. |
| **3** | **Inyectar texto largo / comillas / parámetros malformados sin error 500** (`CP-S4`) | 1) Abrir `/pista/?sesion=abc'--` → devuelve **`HTTP 400`** limpio (`Identificador de sesión inválido.`).<br>2) Abrir `/calendario/?fecha=9999-12-31` → muestra alerta amarilla controlada sin caer.<br>3) En `/clases/nueva/`, escribir en *Objetivo*: `Pase 'controlado' <script>alert(1)</script>` o más de 250 caracteres → escapa el HTML o muestra error de longitud del formulario (**nunca `HTTP 500`**). | Respuestas controladas `400` / `200` con validación de formulario y escape automático de caracteres especiales. |
| **4** | **Revisar estados vacíos** (`CP-F11`) | Ir a `/jugadores/` o `/justificativos/` y filtrar por `q=SIN_COINCIDENCIA_999` o un rango de fechas futuro. | Muestra **`0 resultados: no hay coincidencias.`**, fila informativa de tabla vacía y botón **`Limpiar filtros`** operativo. |
| **5** | **Carga y operación en celular** | Mostrar la URL pública abierta desde el smartphone: abrir el cajón lateral con el botón **Menú**, entrar a `/pista/` y tocar calificaciones `1–10`. | Diseño adaptativo sin desbordamiento roto, botones táctiles de `36×36 px` y guardado inmediato. |

---

## 3. Banco de Respuestas para Preguntas del Profesor (Criterio 3.1.6.14)

1. **«¿Cómo garantizan que un deportista no pueda ver o modificar las rutinas o justificativos de otro compañero cambiando el ID en la URL (IDOR)?»**
   - **Respuesta:** En `student_complete_routine` (`/rutinas/<pk>/completar/`) la consulta filtra simultáneamente por el `pk` de la rutina y por el jugador asociado al `request.user.username` (`get_object_or_404(Rutina, pk=pk, jugador=player)`), devolviendo `404` si el ID pertenece a otro alumno. Igualmente, en `StudentDocumentForm` el `queryset` de evaluaciones se restringe exclusivamente a `Evaluacion.objects.filter(jugador=player)`. Está probado automáticamente en `test_horizontal_isolation_between_students_anti_idor`.

2. **«¿Dónde se guardan los certificados médicos y cómo evitan que alguien con el link directo los descargue sin permiso?»**
   - **Respuesta:** En producción se almacenan en el bucket `huachipato-media` de **Supabase Storage** configurado con `public = false`. No existen URLs públicas directas: toda descarga pasa por las vistas Django `document_file` y `authorization_file` protegidas con `@coach_titular`, que verifican la sesión y rol del usuario, registran la descarga en la tabla `Auditoria` y transmiten el binario desde el servidor.

3. **«¿Qué pasa si eliminan la cuenta de acceso de un jugador o de un entrenador? ¿Se pierden sus evaluaciones o registros de auditoría?»**
   - **Respuesta:** No se pierde ningún dato deportivo. El modelo `Jugador` está desacoplado de `auth.User` (se vinculan por RUT) y los modelos `Prestamo`, `Rutina`, `Justificativo` y `Autorizacion` usan `on_delete=models.PROTECT`. Al eliminar la cuenta en `/cuentas/<id>/eliminar/`, solo se borra la fila en `auth_user` (retirando el login), mientras que en `Auditoria` y `Justificativo.revisado_por` se aplica `on_delete=models.SET_NULL`, preservando el registro histórico y añadiendo un evento del administrador que ejecutó la baja.

4. **«¿Por qué eligieron `PROTECT` en unos modelos y `CASCADE` o `SET_NULL` en otros?»**
   - **Respuesta:** Aplicamos integridad referencial según la regla de negocio:
     - `PROTECT` en `Justificativo`, `Autorizacion`, `Prestamo` y `Rutina` hacia `Jugador`/`Equipo` impide borrar accidentalmente a un deportista o implemento con historial legal o activo.
     - `SET_NULL` en `Auditoria.usuario` y `Justificativo.revisado_por` permite dar de baja cuentas de usuario sin borrar la evidencia de auditoría.
     - En `ClaseEntrenamiento`, el borrado desde la interfaz (`session_delete`) está bloqueado por código salvo cuando `estado == 'programada'` y `not evaluacion_set.exists()`.

5. **«¿Cómo evitan que un mismo par de patines o stick se preste a dos jugadores al mismo tiempo?»**
   - **Respuesta:** A nivel de motor de base de datos definimos una restricción de unicidad parcial en `Prestamo.Meta.constraints`: `UniqueConstraint(fields=['equipo'], condition=Q(devuelto__isnull=True), name='un_prestamo_activo')`. Incluso ante dos solicitudes simultáneas, PostgreSQL garantiza que solo puede existir un préstamo con `devuelto IS NULL` por cada equipo.

6. **«¿Por qué una ausencia no baja el promedio técnico del jugador a cero?»**
   - **Respuesta:** Cuando se marca `asistencia = 'A'`, el backend almacena `0` internamente como marcador de sin calificación, pero tanto en `report_pdf.py` (`mean`) como en el portal (`_skill_mean`) solo se promedian las evaluaciones de sesiones con `estado == 'realizada'`, asistencia presente/atraso (`P`/`T`) y nota `> 0`. Así no se distorsiona la curva técnica por una inasistencia médica.

7. **«¿Cómo aseguran que al correr las pruebas automatizadas no se borren ni ensucien los datos reales de Supabase?»**
   - **Respuesta:** `verificar_proyecto.py` fuerza `DJANGO_SETTINGS_MODULE = 'miproyecto.test_settings'`, el cual bloquea la lectura de `.env` (`patch('dotenv.load_dotenv')`), activa `LOCAL_SQLITE = '1'` con base SQLite en memoria y redirige `MEDIA_ROOT` a un directorio temporal que se destruye al terminar.

8. **«¿Qué discrepancias importantes encontraron al pasar de local a la nube en Vercel y Supabase?»**
   - **Respuesta:** Destacamos tres: (1) el límite de payload de `4,5 MB` en funciones Serverless de Vercel, que resolvimos fijando la validación de archivos en `4 MB` y proponiendo *Presigned URLs* como mejora continua; (2) el manejo de conexiones efímeras Serverless, resuelto con `conn_max_age = 0` y soporte para Transaction Pooler; y (3) la exigencia de una `SECRET_KEY` robusta en producción validada automáticamente en el arranque (`test_secret_key.py`).
