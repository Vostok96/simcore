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

El archivo `docs/endpoints.json` lista las rutas detectadas. El servidor incluido responde con stubs vacios para que la UI no se rompa, pero el trabajo real sera reemplazar esos stubs por el backend ficticio conectado al NAS.

## Recapturar desde SIMCORE

Usar solo para estructura/frontend, no para datos:

```powershell
$env:SIMCORE_SOURCE_USER = "TU_USUARIO_SIMCORE"
$env:SIMCORE_SOURCE_PASS = "TU_PASSWORD_SIMCORE"
python .\tools\capture_simcore_frontend.py
```

La herramienta inicia sesion, descarga paginas de menu y assets publicos. No llama endpoints de listados de pacientes/ordenes.
