# Evidencia de pruebas de control de acceso (RBAC, Autenticación y Anti-IDOR)

Sistema de Seguimiento Deportivo — **CD Huachipato (Hockey en Patines)**.

## 1. Identificación de la ejecución

- **Fecha de ejecución:** 18 de noviembre de 2026 (America/Santiago).
- **Suite automatizada específica:** `seguimiento/test_access_control.py` (`AccessControlTests`, **9 pruebas** dedicadas).
- **Suite completa verificada:** `verificar_proyecto.py` (**60/60 tests aprobados** en `31.442s`, `manage.py check` sin incidencias, `makemigrations --check --dry-run` sin cambios pendientes).
- **Verificación complementaria H5:** `scripts/verificar_h5.py` (**APROBADO**, matriz RBAC, cabeceras HTTP seguras y `0` fugas de `observacion_privada`).
- **Entorno:** Windows, Django 5.2, configuración aislada `miproyecto/test_settings.py` (SQLite en memoria y carpeta de archivos temporal, sin credenciales de producción).
- **Registro bruto de ejecución:** [`docs/evidencias/ejecucion-2026-11-18-control-acceso.txt`](evidencias/ejecucion-2026-11-18-control-acceso.txt).

---

## 2. Matriz de Control de Acceso verificada (Roles × Recursos)

Leyenda de códigos HTTP verificados en servidor:
- `200` / `302` (acción válida): **Acceso permitido**.
- `302 → /accounts/login/`: **Bloqueado por falta de autenticación**.
- `403`: **Acceso denegado por falta de privilegios o CSRF inválido**.
- `404`: **Recurso ajeno aislado (protección anti-IDOR)**.
- `405`: **Método HTTP no permitido (`GET` sobre ruta `POST`-only)**.

| Recurso / Módulo | Anónimo | Alumno | Asistente | Entrenador | Administrador | Superusuario |
|---|---|---|---|---|---|---|
| `/manifest.webmanifest`, `/accounts/login/`, `/registro/` *(cerrado)* | `200` | `200` | `200` | `200` | `200` | `200` |
| `/` *(Dashboard / Portal alumno)* | `302` login | `200` *(solo propio)* | `200` | `200` | `200` | `200` |
| `/mi-justificativo/` y `/rutinas/<id>/completar/` *(propias)* | `302` login | `200` / `302` | Redirige / `404` | Redirige / `404` | Redirige / `404` | Redirige / `404` |
| `/rutinas/<id_ajeno>/completar/` *(de otro deportista)* | `302` login | **`404`** *(anti-IDOR)* | — | — | — | — |
| `/pista/`, `/calendario/`, `/clases/*`, `/evaluaciones/*`, `/reportes/` | `302` login | **`403`** | `200` | `200` | `200` | `200` |
| `/jugadores/`, `/jugadores/<id>/`, `/inventario/`, `/inventario/<id>/prestar/`, `/prestamos/<id>/devolver/`, `/rutinas/` | `302` login | **`403`** | `200` | `200` | `200` | `200` |
| `/justificativos/*`, `/justificativos/<id>/archivo/`, `/justificativos/<id>/revisar/` | `302` login | **`403`** | **`403`** | `200` | `200` | `200` |
| `/autorizaciones/*`, `/autorizaciones/<id>/archivo/` | `302` login | **`403`** | **`403`** | `200` | `200` | `200` |
| `/auditoria/`, `/jugadores/exportar/`, `/agregar/`, `/jugadores/<id>/editar/`, `/jugadores/<id>/acceso/`, `/inventario/nuevo/`, `/inventario/<id>/editar/` | `302` login | **`403`** | **`403`** | `200` | `200` | `200` |
| `/equipo-tecnico/`, `/equipo-tecnico/<id>/gestionar/`, `/cuentas/<id>/eliminar/` *(cuentas no superusuario)* | `302` login | **`403`** | **`403`** | **`403`** | `200` | `200` |
| `/equipo-tecnico/<super>/gestionar/` y `/cuentas/<super>/eliminar/` | `302` login | **`403`** | **`403`** | **`403`** | **`403`** | Protegido *(no auto-borrado)* |

---

## 3. Casos de prueba automatizados ejecutados (`CA-01` a `CA-09`)

### CA-01 — Bloqueo de usuarios anónimos en todas las rutas protegidas
- **Método:** `AccessControlTests.test_anonymous_users_redirected_on_all_protected_routes`
- **Qué se probó:** Solicitudes `GET` y `POST` sin sesión sobre las **37 rutas internas protegidas** del proyecto, además de comprobar `/manifest.webmanifest` y que `POST /registro/` no crea usuarios.
- **Resultado obtenido:** Todas las rutas protegidas redirigieron con `HTTP 302` a `/accounts/login/?next=...`. El conteo de usuarios permaneció intacto tras `POST /registro/`.
- **Estado:** **APROBADO**.

### CA-02 — Restricción total de rutas técnicas para cuentas de Deportista (`Alumno`)
- **Método:** `AccessControlTests.test_student_denied_all_staff_routes_get_and_post`
- **Qué se probó:** Acceso autenticado como deportista a `/` y `/mi-justificativo/` (permitidos), seguido de intentos directos `GET` y `POST` sobre todas las rutas de `@coach`, `@coach_titular` y `@club_admin` (incluyendo guardar evaluaciones JSON, aprobar justificativos, devolver préstamos, eliminar clases y eliminar cuentas).
- **Resultado obtenido:** `200` en sus vistas de portal; **`403 Forbidden`** en todas las rutas técnicas, verificando que ningún registro fue creado, alterado ni eliminado.
- **Estado:** **APROBADO**.

### CA-03 — Frontera de permisos para Profesor Asistente (`ROL_ASISTENTE`)
- **Método:** `AccessControlTests.test_assistant_rbac_boundary_allowed_and_denied`
- **Qué se probó:** Navegación operativa permitida (`pista`, `calendario`, `jugadores`, `inventario`, `rutinas`, `reportes`) frente a intentos `GET` y `POST` sobre vistas sensibles (`justificativos`, `autorizaciones`, `auditoria`, `exportar_jugadores`, alta/edición/acceso de jugadores, alta/edición de equipos y `equipo_tecnico`).
- **Resultado obtenido:** `200` en módulos operativos y **`403 Forbidden`** en todos los recursos sensibles y administrativos.
- **Estado:** **APROBADO**.

### CA-04 — Frontera de permisos para Entrenador Titular (`ROL_ENTRENADOR`)
- **Método:** `AccessControlTests.test_coach_titular_rbac_boundary_allowed_and_denied`
- **Qué se probó:** Acceso a módulos sensibles del club (`justificativos`, descargas privadas, `autorizaciones`, `auditoria`, exportación CSV, edición de jugadores e inventario) frente a intentos `GET` y `POST` sobre `/equipo-tecnico/`, `/equipo-tecnico/<id>/gestionar/` y `/cuentas/<id>/eliminar/`.
- **Resultado obtenido:** `200` en módulos sensibles del club y **`403 Forbidden`** en administración de cuentas.
- **Estado:** **APROBADO**.

### CA-05 — Jerarquía entre Administrador del Club y Superusuario
- **Método:** `AccessControlTests.test_club_admin_and_superuser_privilege_hierarchy`
- **Qué se probó:** Gestión de roles de personal no superusuario por parte de un `Administrador`, junto con intentos de cambiar rol, desactivar, restablecer clave o eliminar a un `Superusuario` o a sí mismo.
- **Resultado obtenido:** Permitió promover a un asistente a entrenador; rechazó con **`403 Forbidden`** toda modificación/eliminación sobre el superusuario y el auto-borrado; impidió auto-desactivación.
- **Estado:** **APROBADO**.

### CA-06 — Aislamiento horizontal entre deportistas (protección Anti-IDOR)
- **Método:** `AccessControlTests.test_horizontal_isolation_between_students_anti_idor`
- **Qué se probó:** Con dos deportistas (`Alpha` y `Beta`), el deportista `Beta` consultó `/`, envió `POST /rutinas/<rutina_alpha>/completar/` e intentó subir un justificativo en `/mi-justificativo/` apuntando al ID de evaluación de `Alpha`. Además, se verificó que ninguno vea `observacion_privada` ni pueda descargar adjuntos por `/justificativos/<id>/archivo/` o `/autorizaciones/<id>/archivo/`.
- **Resultado obtenido:** `0` datos de `Alpha` visibles para `Beta`; **`404`** al intentar completar rutina ajena; error de validación y `0` justificativos creados en intento cruzado; **`403`** en descargas privadas y `0` fugas de `observacion_privada`.
- **Estado:** **APROBADO**.

### CA-07 — Revocación inmediata de cuentas desactivadas (`is_active=False`)
- **Método:** `AccessControlTests.test_deactivated_account_blocked_from_login_and_existing_session`
- **Qué se probó:** Inicio de sesión exitoso con cuenta activa, posterior desactivación (`is_active=False`), reintento con la sesión ya abierta y nuevo intento de autenticación.
- **Resultado obtenido:** La sesión existente perdió acceso de inmediato (`302` hacia login) y el nuevo intento de inicio de sesión fue rechazado.
- **Estado:** **APROBADO**.

### CA-08 — Bloqueo de `GET` en endpoints de mutación (`@require_POST`)
- **Método:** `AccessControlTests.test_post_only_endpoints_reject_get_with_405`
- **Qué se probó:** Peticiones `GET` autenticadas sobre `nueva_sesion`, `guardar_evaluacion`, `acceso_jugador`, `revisar_justificativo`, `devolver`, `gestionar_equipo_tecnico` y `completar_rutina`.
- **Resultado obtenido:** Todas respondieron **`405 Method Not Allowed`**.
- **Estado:** **APROBADO**.

### CA-09 — Exigencia obligatoria de token CSRF en operaciones críticas
- **Método:** `AccessControlTests.test_csrf_enforced_on_sensitive_state_changes`
- **Qué se probó:** Peticiones `POST` con `Client(enforce_csrf_checks=True)` sin token CSRF (autenticado como `Administrador`) sobre `guardar_evaluacion`, `revisar_justificativo`, `acceso_jugador`, `gestionar_equipo_tecnico`, `eliminar_cuenta` y `eliminar_clase`.
- **Resultado obtenido:** Todas fueron rechazadas con **`403 Forbidden`**.
- **Estado:** **APROBADO**.

---

## 4. Cómo reproducir estas pruebas

Ejecución de la suite completa aislada (60 tests, genera informe en `resultados_pruebas/`):

```powershell
.\PROBAR.cmd
```

O ejecutando directamente el verificador con el entorno virtual ya instalado:

```powershell
.\.venv\Scripts\python.exe verificar_proyecto.py
.\.venv\Scripts\python.exe scripts\verificar_h5.py
```

---

## 5. Alcance y límites declarados

- Estas pruebas verifican las reglas de autenticación, autorización en servidor (decoradores RBAC), aislamiento entre deportistas, métodos HTTP y CSRF en un entorno Django aislado.
- No sustituyen pruebas de penetración externas, auditorías de infraestructura cloud (Vercel/Supabase) ni ensayos manuales de usabilidad en producción (documentados aparte en [`docs/plan-pruebas.md`](plan-pruebas.md) y [`docs/cuentas-prueba.md`](cuentas-prueba.md)).
