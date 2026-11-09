# Alcance actual — Bloque 3 (Evaluación 3 / Piloto CD Huachipato)

Portal web desplegable en **Vercel + Supabase** (PostgreSQL + Supabase Storage privado) con soporte PWA instalable y modo local aislado (`LOCAL_SQLITE=1`).

## Funcionalidades vigentes

- **Evaluación en pista (`/pista/`):** asistencia (`Presente`, `Atraso`, `Ausente`, `Justificado`), notas técnicas `1–10` (Frenado, Pase, Tiro), filtro por jugador/RUT, guardado automático asíncrono y **respaldo local en `localStorage`** ante caídas temporales de red en cancha.
- **Planificación y calendario (`/calendario/`):** vistas mensual, semanal y listado, con **repetición semanal (1 a 12 semanas)** al programar entrenamientos futuros y preservación histórica ante cancelaciones.
- **Gestión de deportistas (`/jugadores/`):** validación chilena de **RUT Módulo 11**, historial con gráfico Canvas 2D interactivo, exportación CSV segura y generación/restablecimiento de acceso al portal sin exponer contraseñas en auditoría.
- **Portal del alumno (`/`):** resumen de asistencias y promedio técnico, gráfico evolutivo, **próximos entrenamientos**, **préstamos de equipamiento vigentes**, **estado de autorización de apoderado**, rutinas y envío de justificativos. Las `observacion_privada` nunca se muestran ni exportan al alumno.
- **Cumplimiento documental y auditoría (Ley 19.628):**
  - RBAC mediante grupos (`Administrador`, `Entrenador`, `Asistente`) y vista de administración `/equipo-tecnico/`.
  - Archivos privados PDF/JPG hasta **4 MB** con verificación de firma binaria, huella de integridad **SHA-256**, IP de registro en autorizaciones, trazabilidad de quién aprueba/rechaza justificativos y eliminación del archivo previo al reemplazar una autorización.
  - Descargas autenticadas en servidor (`FileResponse` privado), cabeceras HTTP de seguridad (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`) y cookies `HttpOnly` / `SameSite=Lax`.
- **Inventario del club (`/inventario/`) y reportes (`/reportes/`):** búsqueda rápida de equipamiento/préstamos, estado de conservación al devolver y descarga de informes mensuales PDF/CSV.

## Límites conocidos declarados al cliente

- El registro de autorización de apoderado y su huella SHA-256 acreditan integridad técnica del documento subido, pero no sustituyen la firma electrónica avanzada ni un flujo legal notarial externo.
- No incluye cobros/mensualidades, ficha médica clínica ni notificaciones push/SMS externas (fuera de alcance del proyecto TIHI43).
- El restablecimiento de clave del apoderado/alumno se realiza mediante el cuerpo técnico titular desde el sistema.
