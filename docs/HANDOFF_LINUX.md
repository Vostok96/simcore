# Traspaso a Linux

## Estado al cerrar esta sesion

MUFFIN tiene implementada y verificada localmente, sin Docker, la base de seguridad:

- FastAPI y PostgreSQL 16 definidos en Docker Compose.
- Alembic con migracion `0001_security_foundation`.
- JWT, Argon2, roles, permisos por area y auditoria.
- Datos ficticios idempotentes, script de semilla y prueba de humo.
- Modelo de datos, contrato OpenAPI y documentacion de despliegue.
- Frontend de referencia con identidad MUFFIN, paleta azul noche y modo oscuro.

No hay datos clinicos reales, secretos reales ni despliegue en el NAS.

## Punto exacto pendiente

Completar la fase 1 de `docs/AVANCE_MUFFIN.md`: ejecutar Docker Compose localmente contra PostgreSQL y validar el flujo reproducible. La PC Windows no tiene WSL2 ni Docker Desktop, por eso se traslada la validacion a Linux.

No pasar al NAS ni iniciar los catalogos del MVP hasta que esta validacion termine correctamente.

## Preparacion de Linux

1. Confirmar que Docker Engine y Docker Compose v2 estan disponibles:

   ```bash
   docker --version
   docker compose version
   uname -m
   ```

2. Clonar el repositorio en el disco Linux o, si ya existe, actualizarlo:

   ```bash
   git clone https://github.com/Vostok96/simcore.git MUFFIN
   cd MUFFIN
   ```

   Repositorio existente:

   ```bash
   git pull --ff-only origin main
   ```

3. Crear el entorno local sin reutilizar secretos de NAS:

   ```bash
   cp .env.local.example .env.local
   ```

4. Revisar la composicion resultante antes de iniciar contenedores:

   ```bash
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml config
   ```

## Validacion obligatoria de Compose

Ejecutar desde la raiz del repositorio:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml ps
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python -m app.seed
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/smoke_test.py
```

Resultado esperado:

```text
Local API smoke test passed.
```

Verificar tambien:

```bash
curl http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml logs --tail=100 api postgres
```

El endpoint debe devolver:

```json
{"status":"ok","service":"muffin-api"}
```

## Si la validacion falla

- No modificar los secretos de produccion ni usar el NAS como alternativa.
- Revisar primero `docker compose ... logs api postgres`.
- Corregir compatibilidad de imagen, migracion o variables locales en el repositorio.
- Repetir la prueba desde un volumen limpio:

  ```bash
  docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
  ```

- Ejecutar otra vez todos los comandos de validacion obligatoria.

## Criterio para cerrar fase 1

- Compose crea PostgreSQL y API desde una base vacia.
- Alembic aplica la migracion inicial.
- La semilla puede ejecutarse dos veces sin duplicar registros.
- La prueba de humo completa salud, login JWT y consulta de perfil.
- No aparecen credenciales ni bases de datos locales en Git.

## Siguiente fase despues de Docker

Solo cuando se cumpla el criterio anterior, continuar con fase 2 de `docs/AVANCE_MUFFIN.md`: catalogos minimos del MVP.

Orden: areas, procedencias, servicios, medicos, examenes, muestras, contenedores, relacion examen-muestra, parametros y relacion examen-parametro.

## Documentos de referencia

- `docs/AVANCE_MUFFIN.md`: estado y fases vigentes.
- `docs/DESARROLLO_LOCAL.md`: instrucciones de desarrollo local.
- `docs/MODELO_DATOS_MUFFIN.md`: entidades y reglas del dominio.
- `docs/MUFFIN_API_V1.yaml`: contrato API.
- `docs/DESPLIEGUE_NAS.md`: solo para el despliegue posterior al NAS.
- `docs/IDENTIDAD_VISUAL_MUFFIN.md`: diseno y paletas.
