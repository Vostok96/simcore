# Avance de MUFFIN

Actualizado: 2026-07-15

## Politica de trabajo

MUFFIN se construye, prueba y corrige en local antes de desplegarse en el NAS. El NAS es el destino de preproduccion y produccion, no el entorno de experimentacion.

No se realiza ningun despliegue al NAS hasta cumplir todos los criterios locales de la fase de calidad: migraciones, pruebas funcionales, rendimiento, seguridad, respaldo y restauracion.

## Completado

- Clon local del frontend heredado de SIMCORE, sin datos clinicos reales.
- Identidad visual MUFFIN: diseno operativo, modo claro azul noche y modo oscuro azul tinta.
- Modelo de datos base: `docs/MODELO_DATOS_MUFFIN.md`.
- Contrato API v1: `docs/MUFFIN_API_V1.yaml`.
- Base FastAPI con PostgreSQL, Docker ARM64, Alembic, JWT, Argon2, roles, permisos de area y auditoria.
- Configuracion inicial para el NAS RK3588C con 8 GB de RAM: limites de CPU y memoria, pool reducido y PostgreSQL ajustado para HDD.
- Pruebas locales de hash de contrasena, JWT, migracion, arranque de API y login.

El backend existe solo en local. No hay datos clinicos, secretos reales ni despliegue en el NAS.

## Orden revisado de construccion

### 1. Entorno local reproducible

- Ejecutar Docker Compose localmente contra PostgreSQL antes de usar el NAS.
- Crear datos ficticios de desarrollo y un administrador local no reutilizable.
- Verificar que la migracion se aplique desde una base vacia.
- Mantener `.env` fuera de Git y documentar variables obligatorias.

Este punto es bloqueante para las fases siguientes.

Estado: composicion local, datos ficticios idempotentes y prueba de humo creados. El flujo equivalente sin contenedor ya paso localmente. La validacion de Compose queda pendiente para la proxima sesion Linux; seguir `docs/HANDOFF_LINUX.md`.

### 2. Catalogos minimos del MVP

Los catalogos basicos deben construirse antes de ordenes; no pertenecen a la fase avanzada.

- Areas, procedencias, servicios y medicos.
- Examenes, tipos de muestra, contenedores y relacion examen-muestra.
- Usuarios, roles y permisos por area ya iniciados.
- Parametros de resultado y relacion examen-parametro.

### 3. MVP clinico y trazabilidad de muestra

- Paciente y busqueda por historia clinica.
- Orden y detalle muestra-examen.
- Generacion de numero de orden y codigo de barras.
- Registro de toma, recepcion, destino y eventos de flujo.
- Rechazo, anulacion y reapertura con motivo y auditoria.

El rechazo de muestra y los eventos de flujo se agregan como requisito clinico explicito; no deben quedar implicitos en un campo de estado.

### 4. Resultados y validacion

- Captura de parametros dinamicos por examen.
- Guardado en proceso, validacion preliminar y validacion final.
- Bloqueo posterior a validacion final.
- Reapertura solo con permiso, motivo y evento de auditoria.
- Permisos de validacion por area ya definidos en la base de seguridad.

### 5. Microbiologia avanzada

- Microorganismos, recuentos y comentarios definidos.
- Aislados e identificacion.
- Paneles AST, antibioticos, CMI, interpretacion y metodologia.
- Reglas de consistencia e interpretacion aprobadas por microbiologia.

### 6. Salidas e integraciones

- Informes PDF con version y trazabilidad.
- Etiquetas y codigos de barras.
- Alertas por correo y resultados criticos.
- Conexion con instrumentos y HIS/LIS, si aplica.

Las integraciones deben ser asincronas para no bloquear la operacion clinica.

### 7. Calidad y aceptacion local

- Pruebas unitarias, de API, de flujo completo y de regresion.
- Datos ficticios anonimos para todos los escenarios.
- Pruebas de rendimiento: objetivo inicial p95 menor de 150 ms en consultas y menor de 300 ms en guardados dentro de LAN.
- Revision de permisos, auditoria, sesion, secretos y recuperacion de errores.
- Prueba de respaldo y restauracion de PostgreSQL.
- Manual operativo y criterios de aceptacion con laboratorio.

### 8. Despliegue controlado en NAS

- Construir imagenes Docker compatibles con `linux/arm64`.
- Crear volumenes persistentes, secretos, proxy HTTPS y acceso restringido de red.
- Restaurar un respaldo de prueba en el NAS antes de usar datos reales.
- Ejecutar pruebas de humo y monitorear recursos, errores, tiempos de respuesta y espacio.
- Cargar datos reales solo tras la aceptacion funcional del laboratorio.

## Consideraciones nuevas incorporadas

- El NAS tiene HDD y 8 GB de RAM: el sistema debe evitar listados sin paginacion, consultas N+1, reportes sincronicos y servicios auxiliares innecesarios.
- Las marcas temporales dependen de reloj correcto: el NAS debe mantener NTP activo.
- La privacidad no termina en autenticacion: se requiere retencion de datos, minimizacion de exportaciones y control de acceso a respaldos.
- Las migraciones son parte de cada cambio de modelo y deben probarse contra una base vacia y una base con datos ficticios.
- El estado clinico debe estar representado por eventos auditables, no solo por colores o textos de interfaz.
