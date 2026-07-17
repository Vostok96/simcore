# Contexto para el proximo agente

Fecha de preparacion: 2026-07-15

Repositorio: `Vostok96/simcore`

Carpeta local original en el laboratorio:

```text
C:\Users\LABORATORIO\Documents\AUTOCHECKER\simcore_real_clone
```

## Objetivo del proyecto

Este repositorio contiene una captura local del frontend real de SIMCORE WEB para poder trabajar mejoras fuera del laboratorio, sin llevar datos de pacientes.

La aplicacion original vive en la intranet del laboratorio bajo:

```text
http://192.168.0.220/SIMCORE_WEB/
```

El clon local conserva el prefijo `/SIMCORE_WEB/` para que el frontend se comporte igual y sea mas facil conectarlo a un backend ficticio o a una base simulada en el NAS del usuario.

## Que contiene

- HTML renderizado de las pantallas principales de SIMCORE.
- Bundles CSS y JS entregados por el servidor original.
- Scripts de vistas ubicados en `mirror/SIMCORE_WEB/Scripts/Views`.
- Logo y assets publicos que el servidor entrego correctamente.
- Mapa de rutas en `docs/routes.json`.
- Mapa de assets en `docs/assets.json`.
- Mapa de endpoints detectados en `docs/endpoints.json`.
- Servidor local en `server.py`.
- Script de arranque en `run_local.ps1`.

## Que no contiene

- Base de datos real.
- Ordenes reales.
- Resultados reales.
- Nombres, DNI, HC ni datos clinicos de pacientes.
- Credenciales reales.
- Codigo fuente servidor C#/MVC original, porque ese codigo no se puede descargar por HTTP desde el navegador.

## Estado de privacidad

Antes de subir se reviso y sanitizo el clon:

- No quedaron credenciales reales en los archivos versionados.
- Los inputs ocultos capturados con `session_user_id` fueron cambiados a `local_demo`.
- Se removio una referencia comentada a un DNI de ejemplo en `Mic_orden_Index.js`.
- Se escanearon patrones de DNI de 8 digitos en paginas, scripts, docs y servidor local.

Si se vuelve a capturar desde SIMCORE, repetir un escaneo de privacidad antes de commitear.

## Como ejecutar en casa

Clonar el repo:

```powershell
git clone https://github.com/Vostok96/simcore.git
cd simcore
```

Ejecutar:

```powershell
.\run_local.ps1
```

Abrir:

```text
http://127.0.0.1:8877/SIMCORE_WEB/
```

Tambien se puede lanzar manualmente:

```powershell
python .\server.py
```

## Backend local y NAS

El servidor incluido responde endpoints con stubs vacios para que la interfaz cargue sin datos reales. Ejemplo:

```text
/SIMCORE_WEB/Mic_orden/Obtener
```

Respuesta esperada en modo local:

```json
{
  "data": [],
  "recordsTotal": 0,
  "recordsFiltered": 0,
  "success": true,
  "mensaje": "Modo local: endpoint stub sin datos reales."
}
```

El siguiente trabajo recomendado es reemplazar gradualmente esos stubs por endpoints locales conectados al NAS o a una base ficticia. Usar `docs/endpoints.json` como inventario de endpoints que el frontend intenta llamar.

## Captura realizada

Resumen de la captura guardado en `docs/CAPTURE_REPORT.md`:

- Paginas capturadas: 29
- Paginas con error: 1
- Assets capturados: 33
- Assets con error: 32
- Endpoints detectados: 99

No se invocaron endpoints de listados de pacientes u ordenes reales durante la captura; solo paginas y assets autenticados.

## Errores conocidos de la captura

Una pagina del SIMCORE original respondio HTTP 500 tambien en origen:

```text
/SIMCORE_WEB/Trans_consultas/Microbiologia_proce_servi_medico
```

Varios assets referenciados por CSS respondieron HTTP 404 en el servidor original, sobre todo fuentes FontAwesome, iconos de DataTables y assets de jQuery UI. Estan documentados en `docs/CAPTURE_REPORT.md`.

## Como recapturar desde el laboratorio

No dejar credenciales en archivos. Usar variables de entorno:

```powershell
$env:SIMCORE_SOURCE_URL = "http://192.168.0.220/SIMCORE_WEB/"
$env:SIMCORE_SOURCE_USER = "TU_USUARIO_SIMCORE"
$env:SIMCORE_SOURCE_PASS = "TU_PASSWORD_SIMCORE"
python .\tools\capture_simcore_frontend.py
```

Despues de recapturar:

```powershell
rg -n "\\b\\d{8}\\b|session_user_id|password|pass" .
git status
```

Revisar manualmente cualquier coincidencia antes de subir.

## Historial importante

Inicialmente se habia subido por error un kit teorico del modulo de imagenes. Ese contenido fue eliminado del repo remoto. Luego se preparo este clon real del frontend SIMCORE y se reemplazo el historial remoto con el commit correcto.

Commit base del clon real:

```text
c73602f Capture real SIMCORE frontend without patient data
```

## Recomendaciones para el proximo agente

- No asumir que este repo contiene el backend real de SIMCORE.
- Mantener el prefijo `/SIMCORE_WEB/` mientras se construye el backend simulado.
- Empezar conectando endpoints de solo lectura con datos ficticios.
- Priorizar `Mic_orden`, `Mic_orden_detalle/Resultado_microbiologia`, `Mic_parametro`, `Mic_examen`, `Mic_orga` y reportes de microbiologia.
- No subir capturas nuevas sin escaneo de privacidad.
- Si se agrega backend real local, documentar variables de entorno y nunca versionar `.env`.

## Capturas por rol agregadas

El 2026-07-16 se agregaron capturas separadas por rol:

```text
role_captures/admin/
role_captures/standard_user/
```

Leer primero:

```text
docs/SIMCORE_ROLE_CAPTURE_SUMMARY.md
role_captures/admin/docs/ARCHITECTURE.md
role_captures/standard_user/docs/ARCHITECTURE.md
```

Estas carpetas documentan rutas, assets, formularios y endpoints detectados por perfil. No contienen cuerpos de endpoints de datos ni codigo fuente real del backend.

## Actualizacion MUFFIN

El proyecto ahora incluye una base de backend local en `backend/` con FastAPI, PostgreSQL, Alembic, JWT, Argon2, roles, permisos por area y auditoria. No es codigo del backend original de SIMCORE.

El avance y el orden de construccion vigente estan en `docs/AVANCE_MUFFIN.md`. La politica acordada es construir y probar en local antes de cualquier despliegue al NAS ARM64.

La siguiente sesion se realizara en Linux para validar Docker Compose localmente. Seguir `docs/HANDOFF_LINUX.md` antes de avanzar a catalogos o tocar el NAS.
