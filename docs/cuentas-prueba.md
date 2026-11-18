# Cuentas para la evaluación del sistema

Fecha de revisión: 17 de noviembre de 2026.

URL pública: https://huachipato-cdh.vercel.app/

## Inventario confirmado y pendientes

La información siguiente procede de capturas aportadas por Diego. Ver una cuenta activa no equivale a haber verificado su inicio de sesión con el docente.

| Perfil | Usuario | Evidencia disponible | Preparación para el docente |
|---|---|---|---|
| Administrador del club | `Diego` | Cuenta activa, rol Administrador; sesión administrativa visible. | Cuenta existente del integrante. Preferir una cuenta ficticia dedicada al docente antes de entregar credenciales. |
| Superusuario / administrador | `Daniel` | Cuenta activa con distintivo Superusuario. | Reservada a administración del proyecto; no necesaria para la demo. |
| Entrenador titular | Pendiente de confirmar o crear | El rol aparece en el selector, pero no hay una cuenta de ese perfil visible en las capturas. | Propuesta de usuario: `demo.entrenador`. No se afirma que exista. |
| Profesor asistente | Pendiente de confirmar o crear | El rol aparece en el selector, pero no hay una cuenta de ese perfil visible en las capturas. | Propuesta de usuario: `demo.asistente`. No se afirma que exista. |
| Deportista | Identificador oculto; entrega privada | Una cuenta activa aparece en la lista de deportistas. | Confirmar si es ficticia y entregar su usuario al docente por un canal privado. No publicar RUT personales. |

**Estado de la exigencia «una cuenta de prueba por perfil»: pendiente de completar.** Los roles disponibles y las cuentas realmente creadas son cosas distintas.

## Preparación de las cuentas faltantes

1. Un administrador abre Equipo técnico y permisos.
2. Crea una cuenta ficticia con rol Entrenador Titular y otra con rol Profesor Asistente. Puede usar los nombres propuestos si están disponibles.
3. Para la prueba administrativa, se recomienda crear `demo.admin` con rol Administrador del Club, evitando entregar la cuenta personal de un integrante. Este usuario también es solo una propuesta hasta confirmar su creación.
4. Para deportista, utilizar una ficha ficticia de demostración con acceso habilitado. No usar un RUT real de un menor para la exposición.
5. Guardar las contraseñas temporales por un canal privado, cerrar sesión y verificar cada acceso antes de la exposición. No pegar contraseñas en este archivo, commits, issues o capturas públicas.
6. Actualizar esta tabla con los usuarios confirmados, la fecha y el resultado del ensayo. El superusuario no reemplaza la prueba del perfil mínimo.

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
