# Cuentas para la evaluación del sistema

Fecha de revisión: 17 de noviembre de 2026.

URL pública: https://huachipato-cdh.vercel.app/

## Inventario confirmado y pendientes

La información siguiente procede de capturas aportadas por Diego y de su confirmación del 17 de noviembre de 2026 de que creó las tres cuentas demo con los usuarios y roles sugeridos. Ver una cuenta activa no equivale a haber verificado su inicio de sesión con el docente.

| Perfil | Usuario | Evidencia disponible | Preparación para el docente |
|---|---|---|---|
| Administrador del club | `Diego` | Cuenta activa, rol Administrador; sesión administrativa visible. | Cuenta existente del integrante. Preferir una cuenta ficticia dedicada al docente antes de entregar credenciales. |
| Superusuario / administrador | `Daniel` | Cuenta activa con distintivo Superusuario. | Reservada a administración del proyecto; no necesaria para la demo. |
| Administrador de prueba | `demo.admin` | Creación confirmada por Diego. | Cuenta destinada al docente; inicio de sesión y permisos pendientes de ensayo. |
| Entrenador titular | `demo.entrenador` | Creación confirmada por Diego. | Inicio de sesión y permisos pendientes de ensayo. |
| Profesor asistente | `demo.asistente` | Creación confirmada por Diego. | Inicio de sesión y permisos pendientes de ensayo. |
| Deportista | Identificador oculto; entrega privada | Una cuenta activa aparece en la lista de deportistas. | Confirmar si es ficticia y entregar su usuario al docente por un canal privado. No publicar RUT personales. |

**Estado:** creación de las tres cuentas técnicas demo confirmada. Falta confirmar la cuenta ficticia de deportista y ensayar el ingreso y las restricciones de cada perfil. No se afirma que estos ensayos públicos estén ejecutados.

## Preparación final para el docente

1. Usar `demo.admin`, `demo.entrenador` y `demo.asistente` para la evaluación, conservando las cuentas personales de los integrantes.
2. Confirmar qué cuenta ficticia de deportista se entregará y comunicar su usuario por privado si corresponde a un identificador personal.
3. Cerrar sesión e ingresar con cada cuenta; comprobar una acción permitida y una denegada de la tabla siguiente, también mediante URL directa.
4. Registrar fecha y resultado del ensayo, sin marcar como aprobado lo que no se haya ejecutado.
5. Entregar las contraseñas al docente por un canal privado. No incluirlas en este archivo, commits, issues o capturas públicas.

## Recorrido por perfil

| Perfil | Acción permitida para demostrar | Acción que debe rechazarse |
|---|---|---|
| Administrador | Gestionar cuentas y roles. | Eliminar su propia cuenta o un superusuario. |
| Entrenador | Gestionar jugadores, evaluaciones y justificativos. | Entrar a la administración de equipo técnico. |
| Asistente | Evaluar en pista y consultar calendario/rutinas. | Entrar a justificativos, autorizaciones, auditoría o gestión de cuentas. |
| Deportista | Consultar su portal y completar sus rutinas. | Entrar a equipo técnico o a pantallas de gestión del entrenador. |

Probar las restricciones accediendo también a las rutas directamente; ocultar un botón no demuestra autorización en servidor. Usar registros ficticios para cualquier operación de modificación o eliminación.

## Comprobación pública y móvil

Diego confirmó el 17 de noviembre de 2026 que la URL es pública y que puede ingresar desde un celular. Es una comprobación reportada por el integrante, no una ejecución observada por el asistente. No se registraron modelo del dispositivo, navegador ni resultados de todos los flujos; esos detalles siguen pendientes.

Las contraseñas se entregan al docente por un canal privado acordado por el equipo. Este repositorio público no contiene las credenciales de acceso de producción.
