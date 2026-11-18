# Plan de pruebas: matriz de 15 casos ejecutados

Sistema de Seguimiento Deportivo CD Huachipato. Entrega prevista: 18 de noviembre de 2026.

## Identificación de la ejecución

- Fecha: 17 de noviembre de 2026 (America/Santiago).
- Versión de referencia: `50cf33fa133f09c6701fe34f66086ee4bf920f3d`.
- Entorno: Windows, Django, SQLite en memoria, archivos temporales y cliente de pruebas Django. Sin acceso a producción ni datos reales.
- Ejecución automatizada asistida; revisión humana de evidencias para la entrega: pendiente por Diego y Daniel.
- Resultado de la suite fuente: **50 tests aprobados**, `check` sin incidencias y sin migraciones pendientes. La matriz agrupa escenarios de esa ejecución en **15 casos**, no afirma que sean 15 tests individuales.
- Evidencia: [salida de la ejecución](evidencias/ejecucion-2026-11-17.txt).
- Reproducción: ejecutar `PROBAR.cmd` o `python verificar_proyecto.py` con dependencias instaladas. Se generan datos ficticios aislados automáticamente.

**Alcance del estado:** APROBADO LOCAL significa que las aserciones automatizadas indicadas pasaron. La verificación manual en la URL pública y en celular sigue PENDIENTE. Este documento no acredita que el despliegue esté actualizado ni una certificación de seguridad.

## Matriz resumida

| ID | Caso | Resultado local | Verificación pública |
|---|---|---|---|
| CP-S1 | Autenticación y acceso anónimo | APROBADO LOCAL | PENDIENTE |
| CP-S2 | Control de roles | APROBADO LOCAL | PENDIENTE |
| CP-S3 | Inmutabilidad de un registro cerrado | APROBADO LOCAL | PENDIENTE |
| CP-S4 | Datos malformados sin error 500 | APROBADO LOCAL | PENDIENTE |
| CP-F1 | Alta y edición de jugador | APROBADO LOCAL | PENDIENTE |
| CP-F2 | Asistencia y evaluación | APROBADO LOCAL | PENDIENTE |
| CP-F3 | Clase futura y bloqueo de evaluación | APROBADO LOCAL | PENDIENTE |
| CP-F4 | Cancelación y conservación del historial | APROBADO LOCAL | PENDIENTE |
| CP-F5 | Observaciones privadas | APROBADO LOCAL | PENDIENTE |
| CP-F6 | Rutinas y aislamiento por jugador | APROBADO LOCAL | PENDIENTE |
| CP-F7 | Préstamo y devolución | APROBADO LOCAL | PENDIENTE |
| CP-F8 | Justificativos y privacidad | APROBADO LOCAL | PENDIENTE |
| CP-F9 | Autorizaciones | APROBADO LOCAL | PENDIENTE |
| CP-F10 | Reportes y promedios | APROBADO LOCAL | PENDIENTE |
| CP-F11 | Filtros, CSV y estados vacíos | APROBADO LOCAL | PENDIENTE |

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

Actualización del 17 de noviembre: Diego reportó que la URL es pública y permite ingresar desde un celular. Se confirma únicamente ese alcance; la repetición pública de los 15 casos continúa pendiente. Ver [cuentas y accesos](cuentas-prueba.md).

1. Confirmar que la URL pública corresponde a la versión revisada.
2. Repetir CP-S1 a CP-S4 con cuentas ficticias de los perfiles indicados. No usar cuentas ni documentos reales para operaciones destructivas.
3. En CP-S3, demostrar un **justificativo ya aprobado**: una clase Realizada no equivale a un registro cerrado. Si la pauta exige otra entidad cerrada, validar ese alcance con el docente.
4. Completar la verificación pública de cada fila con fecha/hora, perfil, resultado real y evidencia. No sustituir PENDIENTE por APROBADO sin ejecutar el escenario.
5. Realizar adicionalmente el recorrido desde un celular real: login, navegación, filtros, evaluación, descarga PDF y estados vacíos. Registrar dispositivo/navegador y problemas visuales.
6. Entregar las cuentas por perfil en docs/cuentas-prueba.md; las contraseñas se comparten al docente por un canal privado. Ese documento se prepara por separado.

La prueba de Supabase incluida en la suite utiliza respuestas simuladas. Esta ejecución no verifica la infraestructura de Vercel/Supabase, concurrencia, disponibilidad ni velocidad en redes móviles.
