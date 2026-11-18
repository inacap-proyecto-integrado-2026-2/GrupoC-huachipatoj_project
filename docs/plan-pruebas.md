# Plan de pruebas: matriz de 15 casos ejecutados

Sistema de Seguimiento Deportivo CD Huachipato. Entrega prevista: 18 de noviembre de 2026.

## Identificación de la ejecución

- Fecha: 18 de noviembre de 2026 (America/Santiago).
- Versión de referencia: `beddc8d` (producción Vercel).
- Entorno: Windows, Django, SQLite en memoria, archivos temporales, cliente de pruebas Django y verificación en despliegue público Vercel + Supabase.
- Resultado de la suite fuente: **60 tests aprobados** (`verificar_proyecto.py`), `check` sin incidencias y sin migraciones pendientes, más **5 escenarios de estrés y borde aprobados** (`scripts/prueba_estres.py`) y verificación H5 (`scripts/verificar_h5.py`). La matriz agrupa los escenarios funcionales y de corte en **15 casos**, cubriendo el 100% de los flujos críticos.
- Evidencia: suite automatizada en `resultados_pruebas/`, registros en [`docs/evidencias/`](evidencias/), pruebas de control de acceso en [`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md), análisis de discrepancias y recomendaciones en [`docs/validacion-discrepancias-recomendaciones.md`](validacion-discrepancias-recomendaciones.md) y validación en vivo en `https://huachipato-cdh.vercel.app/`.
- Reproducción: ejecutar `PROBAR.cmd` o `python verificar_proyecto.py` y `python scripts/prueba_estres.py` con dependencias instaladas. Se generan datos ficticios aislados automáticamente.

**Alcance del estado:** APROBADO LOCAL y APROBADO PÚBLICO. Los 15 casos fueron ejecutados tanto en el entorno de pruebas automatizadas como verificados en el despliegue público en producción.

## Matriz resumida

| ID | Caso | Resultado local | Verificación pública |
|---|---|---|---|
| CP-S1 | Autenticación y acceso anónimo | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-S2 | Control de roles (RBAC) | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-S3 | Inmutabilidad de un registro cerrado | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-S4 | Datos malformados sin error 500 | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F1 | Alta y edición de jugador | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F2 | Asistencia y evaluación en pista | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F3 | Clase futura y bloqueo de evaluación | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F4 | Cancelación y conservación del historial | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F5 | Observaciones privadas y confidencialidad | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F6 | Rutinas y aislamiento por jugador | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F7 | Préstamo y devolución de inventario | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F8 | Justificativos y privacidad (Ley 19.628) | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F9 | Autorizaciones de apoderados | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F10 | Reportes y promedios con informe PDF | APROBADO LOCAL | APROBADO PÚBLICO |
| CP-F11 | Filtros, exportación CSV y estados vacíos | APROBADO LOCAL | APROBADO PÚBLICO |

## Detalle reproducible y trazabilidad

### CP-S1 — Autenticación y acceso anónimo

- **Perfil/precondiciones:** Deportista; visitante sin sesión.
- **Pasos ejecutados:** Crear cuenta ficticia; iniciar sesión mediante RUT y contraseña generada; cerrar sesión e intentar abrir páginas protegidas.
- **Resultado esperado:** Ingreso válido autenticado; el visitante es redirigido al login.
- **Resultado obtenido:** Se verificó login HTTP 302 y usuario de sesión; el acceso anónimo fue redirigido.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_player_portal_account_and_rut_login`, `test_permissions`.

### CP-S2 — Control de roles

- **Perfil/precondiciones:** Administrador, entrenador, asistente y deportista.
- **Pasos ejecutados:** Acceder con perfiles de menor privilegio a equipo técnico, documentos y eliminación de cuentas; intentar POST directo.
- **Resultado esperado:** Acciones no autorizadas devuelven 403 y no eliminan cuentas.
- **Resultado obtenido:** Roles restringidos y POST directo rechazados; la cuenta objetivo se conservó.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_rbac_roles_and_staff_management_ui`, `test_non_admin_roles_are_denied_even_with_direct_post`.

### CP-S3 — Inmutabilidad de un registro cerrado

- **Perfil/precondiciones:** Entrenador; justificativo aprobado.
- **Pasos ejecutados:** Crear justificativo aprobado; enviar una nueva revisión para rechazarlo y cambiar su observación; releer documento y asistencia.
- **Resultado esperado:** Se mantienen aprobado, observación original y asistencia justificada.
- **Resultado obtenido:** La solicitud respondió 302 sin modificar estado, observación ni asistencia.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_reviewed_document_cannot_be_reopened_or_reversed`.

### CP-S4 — Datos malformados sin error 500

- **Perfil/precondiciones:** Entrenador.
- **Pasos ejecutados:** Enviar sesion=abc, comillas e identificador largo; fechas 0001-01-01 y 9999-12-31; JSON inválido y objetivo de 251 caracteres.
- **Resultado esperado:** Validación controlada; ningún 500 ni registros parciales; HTML escapado.
- **Resultado obtenido:** Identificadores/JSON rechazados con 400; fechas muestran aviso; texto largo invalida formulario; HTML se escapa.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_invalid_session_identifiers`, `test_calendar_extreme_dates_show_validation`, `test_long_text_and_quotes_are_validated`, `test_malformed_score_payloads_never_change_data`.

### CP-F1 — Alta y edición de jugador

- **Perfil/precondiciones:** Entrenador; RUT ficticio válido.
- **Pasos ejecutados:** Crear jugador, editar categoría e intentar cambiar RUT; probar dígito verificador inválido.
- **Resultado esperado:** Alta y edición válidas; RUT inválido o cambio de identidad rechazado.
- **Resultado obtenido:** Jugador creado, categoría actualizada y RUT original conservado.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_create_update_player`, `test_rut_modulo_11_validation`.

### CP-F2 — Asistencia y evaluación

- **Perfil/precondiciones:** Entrenador; clase realizada y jugador.
- **Pasos ejecutados:** Guardar notas 8/7/9; intentar nota 11; registrar ausencia.
- **Resultado esperado:** Persistencia de notas válidas; rechazo de nota fuera de rango; ausencia sin nota deportiva.
- **Resultado obtenido:** La nota se guardó; valor 11 devolvió 400; ausencia se registró con ceros internos.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_scores_persist_and_validate`.

### CP-F3 — Clase futura y bloqueo de evaluación

- **Perfil/precondiciones:** Entrenador.
- **Pasos ejecutados:** Programar una clase futura e intentar registrar evaluación.
- **Resultado esperado:** Clase programada creada; evaluación bloqueada.
- **Resultado obtenido:** Creación correcta y rechazo HTTP 409 al evaluar.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_create_future_and_block_evaluation`.

### CP-F4 — Cancelación y conservación del historial

- **Perfil/precondiciones:** Entrenador; clase con evaluación.
- **Pasos ejecutados:** Cancelar clase y consultar sus evaluaciones y promedios.
- **Resultado esperado:** Historial conservado; clase cancelada excluida de promedios.
- **Resultado obtenido:** Persistencia y exclusión verificadas en prueba automatizada.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_cancel_preserves_history_and_excludes_average`.

### CP-F5 — Observaciones privadas

- **Perfil/precondiciones:** Entrenador y deportista.
- **Pasos ejecutados:** Guardar observación privada; consultar portal del alumno y PDF.
- **Resultado esperado:** La observación no se muestra al alumno ni en el PDF.
- **Resultado obtenido:** Texto privado ausente en ambas salidas.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_private_observation_not_in_student_or_pdf`.

### CP-F6 — Rutinas y aislamiento por jugador

- **Perfil/precondiciones:** Entrenador y dos cuentas de alumnos.
- **Pasos ejecutados:** Asignar rutina, completarla y consultar con el alumno vinculado y otro usuario.
- **Resultado esperado:** Se conserva el cumplimiento; otro usuario no ve información ajena.
- **Resultado obtenido:** Rutina completada y observaciones visibles solo al alumno vinculado.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_routine_and_student_isolation`.

### CP-F7 — Préstamo y devolución

- **Perfil/precondiciones:** Entrenador; equipo disponible.
- **Pasos ejecutados:** Prestar equipo, intentar préstamo duplicado y registrar devolución.
- **Resultado esperado:** Un solo préstamo activo; devolución libera el equipo.
- **Resultado obtenido:** Préstamo/devolución y protección del préstamo activo comprobados.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_inventory_loan_return`.

### CP-F8 — Justificativos y privacidad

- **Perfil/precondiciones:** Entrenador y deportista.
- **Pasos ejecutados:** Subir documento ficticio, aprobar ausencia e intentar descarga con alumno.
- **Resultado esperado:** Aprobación justifica asistencia; descarga no autorizada rechazada.
- **Resultado obtenido:** Asistencia actualizada y descarga del alumno rechazada con 403.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_documents_and_review`.

### CP-F9 — Autorizaciones

- **Perfil/precondiciones:** Entrenador y usuario sin permiso.
- **Pasos ejecutados:** Intentar archivo inválido; registrar autorización con PDF ficticio válido; editar su estado e intentar descarga no autorizada.
- **Resultado esperado:** Registro y edición válidos; archivo inválido y descarga indebida rechazados.
- **Resultado obtenido:** Validaciones y descarga protegida comprobadas.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_authorization_upload_edit_and_private_download`.

### CP-F10 — Reportes y promedios

- **Perfil/precondiciones:** Entrenador; evaluaciones de prueba.
- **Pasos ejecutados:** Generar reporte mensual; comparar promedio excluyendo ausencia, cero y clases no realizadas.
- **Resultado esperado:** Cálculo correcto y selección del mes/categoría.
- **Resultado obtenido:** Promedios y selección comprobados; PDF generado en la suite.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_average_and_month_category_filter`, `test_private_observation_not_in_student_or_pdf`.

### CP-F11 — Filtros, CSV y estados vacíos

- **Perfil/precondiciones:** Entrenador.
- **Pasos ejecutados:** Combinar filtros de cuenta/categoría/búsqueda; exportar CSV; invertir desde/hasta y probar fecha sin coincidencias.
- **Resultado esperado:** CSV coincide con selección; rangos inválidos muestran error y cero resultados.
- **Resultado obtenido:** Pantalla y CSV coinciden; fechas inválidas muestran mensaje y contador cero.
- **Estado:** APROBADO LOCAL.
- **Evidencia automatizada:** `test_accounts_and_csv_match`, `test_date_forms_render_and_reject_invalid_ranges`, `test_document_date_type_category_and_inclusive_end`.

## Cierre para la exposición

Actualización del 18 de noviembre de 2026: Verificación pública completada en `https://huachipato-cdh.vercel.app/` en móvil y escritorio. Se validaron los 15 casos de uso incluyendo los 4 casos de corte de seguridad (CP-S1 a CP-S4), la suite automatizada de **60 tests (100% aprobada)**, la suite de **estrés y borde (`scripts/prueba_estres.py`, 5/5 escenarios aprobados con 150 deportistas y 332,3 ops/s)**, la matriz de control de acceso en [`docs/pruebas-control-acceso.md`](pruebas-control-acceso.md), el análisis de discrepancias y recomendaciones en [`docs/validacion-discrepancias-recomendaciones.md`](validacion-discrepancias-recomendaciones.md) y los perfiles de demostración documentados en [`docs/cuentas-prueba.md`](cuentas-prueba.md).

1. URL pública operativa en Vercel con base de datos en Supabase (PostgreSQL).
2. Los 4 casos de corte de seguridad (CP-S1 a CP-S4) verificados: autenticación por RUT, RBAC estricto (403) + anti-IDOR, inmutabilidad de registros cerrados y validación sin error 500 ante entradas malformadas.
3. Calendario deportivo poblado con clases realizadas, programadas y canceladas (historial y promedios).
4. Evaluaciones en pista con asistencia, notas técnicas (1–10) y observaciones privadas operativas.
5. Cuentas de demostración documentadas en `docs/cuentas-prueba.md`; contraseñas compartidas al docente por canal privado.
6. Comparación detallada Esperado vs. Obtenido, análisis de las 7 discrepancias detectadas (`D-01` a `D-07`) y 7 recomendaciones de mejora continua (`REC-01` a `REC-07`) documentadas en [`docs/validacion-discrepancias-recomendaciones.md`](validacion-discrepancias-recomendaciones.md).

La prueba de Supabase incluida en la suite unitaria utiliza respuestas simuladas. Esta ejecución automatizada local se complementa con la verificación pública en Vercel/Supabase.
