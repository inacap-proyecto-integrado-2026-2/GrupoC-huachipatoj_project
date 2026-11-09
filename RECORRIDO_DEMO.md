# Recorrido de demostración — CD Huachipato

Este guion aplica sobre un entorno local aislado con datos ficticios (`LOCAL_SQLITE=1` + `manage.py cargar_demo`). Ningún archivo de ejemplo tiene validez médica ni legal real.

1. **Dashboard (`/`) y RBAC:** mostrar los KPIs del club, el menú lateral limpio y la sección **Equipo técnico (`/equipo-tecnico/`)** para diferenciar permisos entre `Administrador`, `Entrenador` y `Asistente`.
2. **Plantilla de jugadores (`/jugadores/`):** filtrar por categoría (`Escuelita`, `Sub-15`, `Adulta`) o buscar un jugador `[DEMO]`. Mostrar validación de RUT chileno Módulo 11, estado de autorización/portal y exportación CSV.
3. **Calendario (`/calendario/`):** alternar vistas **Mes**, **Semana** y **Listado**. Crear una clase usando **repetición semanal** (ej. 3 semanas) y verificar cómo se programan automáticamente.
4. **Evaluación en pista (`/pista/`):** abrir una sesión `Realizada`, mostrar alertas de autorización, marcar asistencia (`Presente`, `Atraso`, `Ausente`), asignar notas `1–10` y agregar una **observación privada**. Comprobar el guardado automático y el banner de **cola offline local** en caso de desconexión.
5. **Evolución e informes (`/jugadores/<id>/` y `/reportes/`):** revisar el gráfico interactivo (tocar un punto para ver el detalle), usar el atajo **Informe PDF del mes** y comprobar que `observacion_privada` nunca aparece en PDF/CSV ni en el portal alumno.
6. **Justificativos y Autorizaciones (`/justificativos/`, `/autorizaciones/`):** revisar un justificativo pendiente con nota de revisión, comprobar su **huella SHA-256** (límite 4 MB) y verificar cómo una aprobación cambia automáticamente la asistencia a `Ausente justificado`.
7. **Inventario del club (`/inventario/`):** buscar por código o nombre, registrar un préstamo y luego registrar la devolución actualizando el estado de conservación del equipo.
8. **Portal del deportista (`/` como alumno):** iniciar sesión con el RUT de un jugador demo (sin puntos ni guión), ver su gráfico personal, **próximos entrenamientos**, **préstamos activos**, **estado de autorización**, completar una rutina y enviar un justificativo.
