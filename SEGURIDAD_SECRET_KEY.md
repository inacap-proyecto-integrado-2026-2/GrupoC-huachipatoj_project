# Validación de SECRET_KEY

En Vercel (incluidos Preview y Production) o con DEBUG=False, el inicio exige una SECRET_KEY de al menos 50 caracteres útiles, al menos 5 caracteres distintos y sin el prefijo django-insecure-. Estos controles siguen los criterios básicos de security.W009 de Django; no pueden demostrar que una clave sea aleatoria o que nunca se haya filtrado.

En desarrollo local con DEBUG=True se conserva el comportamiento anterior. Las pruebas aisladas generan una clave efímera sin usar secretos del servidor.

## Antes de integrar o desplegar

1. En Vercel, abrir el proyecto y Settings → Environment Variables.
2. Comprobar que SECRET_KEY está configurada para Production y los entornos Preview que se utilicen. No compartir su valor en capturas, chat, Git ni registros.
3. Si ya existe una clave privada adecuada, conservarla. Si falta o es conocida/insegura, generar una nueva en un entorno privado y guardarla únicamente en Vercel. Coordinar el cambio: las sesiones y enlaces firmados existentes pueden quedar invalidados.
4. Validar un despliegue Preview antes de integrar a main. No reemplazar la clave real por la que usan las pruebas.

Comando para generar una clave en una terminal privada con Django instalado (muestra el secreto en esa terminal; no ejecutarlo en registros compartidos):

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Una variable presente no demuestra que su valor sea adecuado. La validación de arranque lo comprueba sin incluirlo en el mensaje de error. Un despliegue sin clave válida fallará intencionalmente; por eso debe verificarse la configuración antes de publicar.

Pruebas: ejecutar PROBAR.cmd. seguimiento/test_secret_key.py cubre claves ausentes/débiles, Vercel con DEBUG, claves válidas, desarrollo local y errores que no revelan el valor.

Referencia: https://docs.djangoproject.com/en/5.2/ref/checks/#security
