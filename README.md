# CD Huachipato — Portal de Seguimiento Deportivo (Hockey en Patines)

**Sitio en producción (Vercel):** <https://huachipato-cdh.vercel.app/>

Aplicación web responsiva e instalable (PWA) desarrollada para el cuerpo técnico y deportistas de la **Rama de Hockey en Patines del Club Deportivo Huachipato** (Proyecto Integrado TIHI43 · INACAP).

Permite registrar asistencia y calificaciones técnicas en tiempo real desde la pista, programar entrenamientos semanales, controlar equipamiento en préstamo, resguardar justificativos/autorizaciones bajo criterios de protección de datos personales y generar reportes mensuales en PDF y CSV.

---

## Arquitectura y stack tecnológico

- **Backend:** Django 5.2.17 (Python 3.11+) con autenticación dual (usuario técnico o RUT chileno flexible con/sin puntos ni guión vía `RutAuthenticationBackend`) y control de acceso basado en roles (**RBAC**: `Administrador`, `Entrenador`, `Asistente`, `Alumno`).
- **Base de datos:** PostgreSQL en **Supabase** (`DATABASE_URL`) para producción/despliegue; SQLite local aislado mediante `LOCAL_SQLITE=1` para desarrollo y pruebas.
- **Almacenamiento privado de archivos:** **Supabase Storage** (`seguimiento/storage.py`) para documentos PDF/JPG de hasta **4 MB** (compatibles con Vercel) con validación de firma binaria, huella de integridad **SHA-256** y descarga autenticada en servidor (sin URLs públicas).
- **Frontend:** Plantillas Django + CSS propio (`styles.css`), Vanilla JS (`pista.js`, `history.js`, `layout.js`), gráficos Canvas 2D interactivos, cola offline en `localStorage` para evaluación en pista y manifiesto PWA (`/manifest.webmanifest` + escudo SVG).
- **Despliegue:** **Vercel** con **WhiteNoise** para archivos estáticos.

---

## Módulos principales

| Módulo | Ruta principal | Descripción |
|---|---|---|
| **Dashboard operativo** | `/` | KPIs del club, próxima sesión en pista, préstamos activos y alertas de pendientes (filtrados según rol RBAC). |
| **Evaluación en pista** | `/pista/` | Grilla táctil en vivo (`Presente`, `Atraso`, `Ausente`, `Justificado`), notas `1–10` en Frenado/Pase/Tiro, observaciones privadas, alertas de autorización y **cola local en `localStorage`** ante pérdida de señal. |
| **Calendario** | `/calendario/` | Vistas Mensual, Semanal y Listado; programación individual o **repetición semanal (1 a 12 semanas)**; cancelación conservando historial. |
| **Plantilla e historial** | `/jugadores/` | Registro con validación chilena **RUT Módulo 11**, historial con gráfico interactivo, atajo a PDF mensual, creación/reset de clave de portal y exportación CSV segura. |
| **Portal del deportista** | `/` *(alumno)* | Resumen personal, evolución técnica, próximos entrenamientos, préstamos de equipamiento vigentes, estado de autorización, rutinas y carga de justificativos (sin acceso a `observacion_privada`). |
| **Justificativos y Autorizaciones** | `/justificativos/`, `/autorizaciones/` | Acceso exclusivo para `Entrenador` y `Administrador`. Archivos PDF/JPG hasta **4 MB**, huella **SHA-256**, IP de registro en autorizaciones y trazabilidad de revisor. |
| **Inventario del club** | `/inventario/` | Búsqueda por código/equipo/deportista, registro de préstamos únicos activos y devolución con actualización de conservación (`Bueno`, `Desgastado`, `En reparación`). |
| **Reportes y Auditoría** | `/reportes/`, `/auditoria/` | Descarga mensual en PDF (ReportLab) y CSV sin observaciones privadas ni ceros por ausencia, más bitácora de auditoría. |
| **Equipo técnico (RBAC)** | `/equipo-tecnico/` | Alta de cuentas técnicas, cambio de rol (`Administrador`, `Entrenador`, `Asistente`), activación/desactivación y restablecimiento de clave para administradores. |

---

## Inicio rápido en local (Windows — Modo Seguro SQLite)

Para trabajar sin modificar la base de datos en Supabase aunque exista `.env`, usa el iniciador incluido (define `LOCAL_SQLITE=1` automáticamente):

```powershell
.\INICIAR.cmd
```

Luego abre `http://127.0.0.1:8000/`.

Si ejecutas comandos `manage.py` manualmente en PowerShell:

```powershell
$env:LOCAL_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

> **Precaución:** Nunca ejecutes `cargar_demo` sin `$env:LOCAL_SQLITE = "1"` si tienes un `.env` conectado a la base real en Supabase.

---

## Pruebas automatizadas y verificación H5

### 1. Ejecutor aislado de pruebas (sin `.env` ni BD local)

```powershell
.\PROBAR.cmd
```

O si ya tienes el entorno creado:

```powershell
.\.venv\Scripts\python.exe verificar_proyecto.py
```

Ejecuta `check`, `makemigrations --check --dry-run` y la suite de pruebas usando [`miproyecto/test_settings.py`](miproyecto/test_settings.py) (SQLite en memoria y almacenamiento temporal descartable), guardando un informe en `resultados_pruebas/`. Más detalles en [`PRUEBAS_AUTOMATIZADAS.md`](PRUEBAS_AUTOMATIZADAS.md).

### 2. Verificación de rendimiento (<1 s), seguridad HTTP y RBAC

```powershell
.\.venv\Scripts\python.exe scripts\verificar_h5.py
```

Para auditar cabeceras HTTP y disponibilidad GET de solo lectura sobre el sitio publicado en Vercel:

```powershell
.\.venv\Scripts\python.exe scripts\verificar_h5.py --url https://huachipato-cdh.vercel.app
```

---

## Variables de entorno (Vercel / `.env`)

Consulta la plantilla [`.env.example`](.env.example). En producción se requieren:

- `SECRET_KEY` (clave privada aleatoria propia; en Vercel/`DEBUG=False` exige al menos **50 caracteres útiles**, **5 distintos** y sin prefijo `django-insecure-` — ver [`SEGURIDAD_SECRET_KEY.md`](SEGURIDAD_SECRET_KEY.md))
- `DEBUG=False`
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` (ej. `.vercel.app` / `https://*.vercel.app`)
- `DATABASE_URL` (PostgreSQL de Supabase — Transaction Pooler `:6543` con SSL)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET`

Al desplegar cambios que incluyan nuevas migraciones de modelos, aplica `manage.py migrate` contra Supabase antes o junto con el push a `main`.

---

## Documentación adicional del repositorio

- [`LEEME.md`](LEEME.md) — Guía operativa completa de módulos y ejecución local.
- [`PRUEBAS_AUTOMATIZADAS.md`](PRUEBAS_AUTOMATIZADAS.md) — Alcance y límites del ejecutor aislado `PROBAR.cmd` (38 tests).
- [`SEGURIDAD_SECRET_KEY.md`](SEGURIDAD_SECRET_KEY.md) — Requisitos y gestión segura de `SECRET_KEY` en Vercel y desarrollo local.
- [`ALCANCE_ACTUAL.md`](ALCANCE_ACTUAL.md) — Alcance funcional vigente y límites declarados del proyecto.
- [`COMPARTIR.md`](COMPARTIR.md) — Instrucciones para compartir en local o desplegar en Vercel + Supabase.
- [`RECORRIDO_DEMO.md`](RECORRIDO_DEMO.md) — Guion paso a paso de demostración con datos `DEMO`.

### Eliminar cuentas

Solo Administrador puede eliminar cuentas desde Equipo técnico y permisos. Selecciona Eliminar cuenta y escribe el usuario exacto en la confirmación. No se permite eliminar la cuenta propia ni superusuarios. La eliminación retira el acceso y conserva la ficha deportiva, evaluaciones, rutinas y documentos; las referencias históricas al usuario eliminado quedan vacías. Se registra la acción del administrador en auditoría.
