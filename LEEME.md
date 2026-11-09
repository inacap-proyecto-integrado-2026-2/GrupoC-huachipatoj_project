# CD Huachipato · Sistema de Seguimiento Deportivo (Hockey en Patines)

Aplicación web responsiva (Django 5.2 + PWA instalable) para el cuerpo técnico y deportistas del **Club Deportivo Huachipato — Rama Hockey en Patines**.

---

## Arquitectura actual (Producción y Local)

- **Backend:** Django 5.2.17 (`miproyecto/`, `seguimiento/`) con autenticación dual (usuario técnico o RUT chileno con/sin puntos y guión mediante `RutAuthenticationBackend`) y control de acceso basado en roles (**RBAC**: `Administrador`, `Entrenador`, `Asistente` y `Alumno`).
- **Base de datos en producción:** PostgreSQL en **Supabase** (`DATABASE_URL` / pooler compatible con Vercel Serverless).
- **Almacenamiento privado en producción:** **Supabase Storage** (`seguimiento/storage.py`) para respaldos PDF/JPG de justificativos y autorizaciones (sin rutas públicas; descarga auditada vía backend hasta 4 MB por archivo con huella SHA-256).
- **Despliegue:** **Vercel** (`vercel.json`, `api/wsgi.py`, archivos estáticos con WhiteNoise).
- **Modo local aislado (`LOCAL_SQLITE=1`):** Forzado por defecto en `INICIAR.cmd` para trabajar con `db.sqlite3` y `private_media/` locales sin tocar la base de datos ni el almacenamiento en la nube.

---

## Ejecutar en Windows (Modo Local Seguro)

```powershell
.\INICIAR.cmd
```

Si ejecutas comandos `manage.py` manualmente en PowerShell y tienes `.env` configurado con Supabase, activa antes la bandera de aislamiento local para no modificar producción por accidente:

```powershell
$env:LOCAL_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Para inicializar un entorno local limpio con datos ficticios y cuenta de administrador:

```powershell
$env:LOCAL_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
```

---

## Módulos implementados

1. **Dashboard operativo (`/`)**: KPIs, próxima sesión en pista, préstamos activos y pendientes de revisión (documentos sensibles ocultos para `Asistente`).
2. **Evaluación en pista (`/pista/`)**: matriz táctil en vivo (`Presente`, `Atraso`, `Ausente`, `Ausente justificado`), escalas `1–10` de Frenado, Pase y Tiro, búsqueda por nombre/RUT, acción masiva «Marcar pendientes como Presente», alertas de autorización de apoderado y **cola offline local en `localStorage`** cuando falla la señal en cancha.
3. **Calendario (`/calendario/`)**: vistas Mensual, Semanal y Listado; creación individual o **repetición semanal de 1 a 12 clases**; cancelación segura preservando historial.
4. **Plantilla de jugadores (`/jugadores/`)**: ficha con validación **RUT Módulo 11**, creación/restablecimiento de acceso al portal, historial evolutivo con gráfico Canvas 2D interactivo, atajo al informe PDF mensual y exportación CSV protegida contra inyección de fórmulas.
5. **Portal del deportista (`/`)**: vista personal con gráfico técnico, próximos entrenamientos, equipamiento en préstamo activo, estado de autorización de apoderado, rutinas asignadas y envío de justificativos médicos/académicos (sin acceso a `observacion_privada`).
6. **Justificativos y Autorizaciones (`/justificativos/`, `/autorizaciones/`)**: acceso restringido a `Entrenador` y `Administrador`, límite de **4 MB** (seguro para Vercel), validación de firma binaria PDF/JPG, cálculo de **huella SHA-256**, limpieza de archivos reemplazados, registro de IP en autorizaciones y trazabilidad de revisor (`revisado_por` y nota).
7. **Inventario del club (`/inventario/`)**: búsqueda por código/equipo/deportista, registro de préstamos únicos activos y devolución con actualización del estado de conservación (`Bueno`, `Desgastado`, `En reparación`).
8. **Reportes mensuales (`/reportes/`) y Auditoría (`/auditoria/`)**: generación de PDF con `ReportLab` y CSV por jugador o categoría, más bitácora de auditoría administrativa.
9. **Equipo técnico y roles (`/equipo-tecnico/`)**: creación y gestión de cuentas técnicas (`Administrador`, `Entrenador`, `Asistente`) sin entrar al panel `/admin/`.

---

## Validación y pruebas automatizadas

```powershell
$env:LOCAL_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py test seguimiento -v 2
.\.venv\Scripts\python.exe scripts\verificar_h5.py
```
