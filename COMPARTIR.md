# Guía para compartir y desplegar CD Huachipato

## Opción A — Uso inmediato vía enlace web (Producción Vercel + Supabase)

La aplicación está configurada para operar en la nube compartiendo una única base de datos PostgreSQL y un bucket privado en Supabase Storage:

1. Entrega al cuerpo técnico la URL de producción en **Vercel**: <https://huachipato-cdh.vercel.app/>.
2. Ingresa con la cuenta administrador para crear las cuentas de entrenadores y asistentes en **Equipo técnico (`/equipo-tecnico/`)** según su rol (`Entrenador` o `Asistente`).
3. En un teléfono Android/iPhone, abre el enlace en Chrome o Safari y elige **«Añadir a pantalla de inicio»** (utiliza `manifest.webmanifest` y el escudo `cdh-icon.svg`).
4. Antes de cualquier despliegue con cambios de esquema en `main`, aplica primero las migraciones contra Supabase:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

---

## Opción B — Prueba supervisada local en Windows (Sin afectar producción)

1. Copia el repositorio (`Huachipato-prueba`) en el equipo (sin incluir `.env`, `db.sqlite3` ni `private_media/` si se entregará limpio).
2. Ejecuta `.\INICIAR.cmd`. El script activa automáticamente `LOCAL_SQLITE=1`, crea `.venv`, instala dependencias, migra SQLite local y levanta `http://127.0.0.1:8000/`.
3. Si la base local está vacía, abre otra terminal PowerShell y ejecuta:

```powershell
$env:LOCAL_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
```

> **Importante:** Nunca ejecutes `cargar_demo` sin `$env:LOCAL_SQLITE = "1"` si existe un archivo `.env` apuntando a la base real del club, para no mezclar datos ficticios en producción.

---

## Variables de entorno requeridas en Vercel / `.env`

- `SECRET_KEY` (clave secreta larga y única)
- `DEBUG=False` (en producción)
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` (incluyendo dominio propio o `.vercel.app`)
- `DATABASE_URL` (conexión Supabase Transaction Pooler `:6543` con SSL)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_BUCKET` (bucket privado en Supabase Storage)
