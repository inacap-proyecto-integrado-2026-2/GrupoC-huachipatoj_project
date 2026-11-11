# Comprobación automatizada de Huachipato

En Windows, con Python instalado, abrir `PROBAR.cmd`. Crea un entorno exclusivo, instala requirements-dev.txt (requiere Internet) y ejecuta verificar_proyecto.py. No inicia el servidor web.

Con las dependencias ya instaladas también se puede ejecutar:

```powershell
.\.venv-pruebas\Scripts\python.exe verificar_proyecto.py
```

El ejecutor comprueba la configuración de Django, detecta cambios de modelos sin migración y descubre los tests de seguimiento. Incluye los 27 métodos funcionales originales y 5 nuevos métodos de validación de SECRET_KEY en test_secret_key.py.

Las pruebas abarcan páginas, evaluaciones, permisos, préstamos, rutinas, documentos, RUT, cuentas, portal del jugador, calendario, reportes y roles. Supabase Storage se prueba mediante respuestas simuladas, no contra la nube real.

Cada ejecución deja un informe con el detalle, errores y resultado final en resultados_pruebas. Un fallo devuelve código 1. No se ocultan ni corrigen automáticamente los problemas.

La configuración exclusiva miproyecto/test_settings.py desactiva la carga de .env, selecciona SQLite en memoria y usa una carpeta temporal para los archivos. No usa la base local de la aplicación ni credenciales de producción. Los datos de prueba se descartan al finalizar.

Pasar esta suite no demuestra cobertura total, funcionamiento visual en navegador, rendimiento con muchos usuarios, seguridad del despliegue o cumplimiento ISO/OWASP. Estas comprobaciones necesitan pruebas y evidencias adicionales.
