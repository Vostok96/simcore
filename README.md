# SIMCORE WEB frontend clone

Captura del frontend real de `http://192.168.0.220/SIMCORE_WEB/` para trabajar localmente sin datos de pacientes.

Este repositorio contiene:

- HTML renderizado de las pantallas principales de SIMCORE.
- Bundles CSS/JS que entrega el servidor.
- Scripts de vistas de `Scripts/Views`.
- Imagenes y recursos publicos encontrados.
- Mapa de rutas y endpoints usados por el frontend.
- Servidor local para montar la captura bajo `/SIMCORE_WEB/`.

No contiene:

- Base de datos real.
- Ordenes reales.
- Resultados reales.
- Nombres/DNI/HC de pacientes.
- Credenciales reales.
- Codigo servidor C#/MVC, porque ese codigo no se entrega por HTTP.

## Ejecutar

```powershell
cd simcore
.\run_local.ps1
```

Abrir:

```text
http://127.0.0.1:8877/SIMCORE_WEB/
```

El servidor local mantiene las mismas rutas `/SIMCORE_WEB/...` para que el backend ficticio de casa pueda responder endpoints compatibles.

## Backend local/NAS

El frontend espera endpoints como:

```text
/SIMCORE_WEB/Mic_orden/Obtener
/SIMCORE_WEB/Mic_orden/Guardar
/SIMCORE_WEB/Mic_parametro/Obtener
/SIMCORE_WEB/Mic_orden_detalle_res/Guardar
```

El archivo `docs/endpoints.json` lista las rutas detectadas. El servidor incluido responde con stubs vacios para que la UI no se rompa. El backend real de MUFFIN se esta construyendo localmente en `backend/` y sustituira esos stubs de forma gradual despues de sus pruebas locales.

## Estado de MUFFIN

El avance, la politica de desarrollo local antes del NAS y el orden de construccion estan documentados en `docs/AVANCE_MUFFIN.md`.

La guia de continuacion para la proxima sesion Linux esta en `docs/HANDOFF_LINUX.md`.

## Capturas por rol

Tambien se agregaron capturas separadas por perfil para estudiar permisos, rutas, assets y endpoints visibles:

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

Estas capturas no guardan respuestas de datos/listados ni codigo fuente real del backend; documentan la arquitectura observable desde HTTP.

## Recapturar desde SIMCORE

Usar solo para estructura/frontend, no para datos:

```powershell
$env:SIMCORE_SOURCE_USER = "TU_USUARIO_SIMCORE"
$env:SIMCORE_SOURCE_PASS = "TU_PASSWORD_SIMCORE"
python .\tools\capture_simcore_frontend.py
```

La herramienta inicia sesion, descarga paginas de menu y assets publicos. No llama endpoints de listados de pacientes/ordenes.
