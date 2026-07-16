# Desarrollo local de MUFFIN

## Objetivo

Validar toda correccion en local antes de desplegarla al NAS. El entorno local reproduce la API FastAPI y PostgreSQL mediante Docker Compose, pero usa datos estrictamente ficticios.

## Requisitos

- Docker Desktop con backend WSL2 activo.
- Docker Compose v2.
- Puesto `8000` libre o `MUFFIN_API_PORT` definido en `.env.local`.

Si WSL2 no esta instalado, habilitarlo desde una terminal Windows con privilegios de administrador y reiniciar antes de instalar o iniciar Docker Desktop. No avanzar al NAS para sustituir esta validacion local.

## Primer arranque

1. Copiar `.env.local.example` a `.env.local`.
2. Mantener las credenciales como valores exclusivos de desarrollo; nunca reutilizarlas en NAS o produccion.
3. Ejecutar:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build
   ```

4. Crear datos ficticios idempotentes:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python -m app.seed
   ```

5. Ejecutar la prueba de humo:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/smoke_test.py
   ```

La prueba confirma migracion, salud de API, login JWT y el usuario ficticio `dev-admin`.

## Datos ficticios incluidos

| Usuario | Rol | Uso |
| --- | --- | --- |
| `dev-admin` | `ADMIN` | Administracion y pruebas de permisos. |
| `dev-entry` | `ENTRY` | Registro de solicitudes. |
| `dev-processor` | `PROCESSOR` | Procesamiento y permisos de validacion en microbiologia. |

Areas: `MICROBIOLOGY` y `RECEPTION`.

## Reinicio limpio

Para eliminar toda la base ficticia local:

```powershell
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
```

Luego repetir el primer arranque. Nunca ejecutar este comando contra los volumenes del NAS.
