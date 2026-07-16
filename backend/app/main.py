from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import SessionLocal
from app.routers import admin, auth
from app.security import hash_password
from app.services import bootstrap_security_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.ensure_secure_production_settings()
    with SessionLocal() as db:
        password = settings.bootstrap_admin_password.get_secret_value() if settings.bootstrap_admin_password else None
        bootstrap_security_data(
            db,
            settings.bootstrap_admin_username,
            password,
            settings.bootstrap_admin_given_name,
            settings.bootstrap_admin_family_name,
            hash_password,
        )
    yield


app = FastAPI(title="MUFFIN API", version="0.1.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "service": "muffin-api"}
