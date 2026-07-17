"""Development-only seed data for local MUFFIN environments."""

import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import LaboratoryArea, Role, User, UserAreaPermission
from app.security import hash_password
from app.services import bootstrap_security_data, record_audit


DEVELOPMENT_USERS = (
    ("dev-admin", "Dev", "Administrator", ("ADMIN",)),
    ("dev-entry", "Dev", "Entry", ("ENTRY",)),
    ("dev-processor", "Dev", "Processor", ("PROCESSOR",)),
)

DEVELOPMENT_AREAS = (
    ("MICROBIOLOGY", "Microbiology", "MICROBIOLOGY"),
    ("RECEPTION", "Specimen reception", "MICROBIOLOGY"),
)


def get_development_password() -> str:
    password = os.getenv("DEV_SEED_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must contain at least 12 characters.")
    return password


def seed() -> None:
    password = get_development_password()
    with SessionLocal() as db:
        bootstrap_security_data(db, None, None, "", "", hash_password)

        areas: dict[str, LaboratoryArea] = {}
        for code, name, section in DEVELOPMENT_AREAS:
            area = db.scalar(select(LaboratoryArea).where(LaboratoryArea.code == code))
            if not area:
                area = LaboratoryArea(code=code, name=name, section=section)
                db.add(area)
                db.flush()
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="laboratory_area",
                    entity_id=area.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"code": area.code},
                )
            areas[code] = area

        for username, given_name, family_name, role_codes in DEVELOPMENT_USERS:
            user = db.scalar(select(User).where(User.username == username))
            if user:
                continue
            roles = list(db.scalars(select(Role).where(Role.code.in_(role_codes))))
            user = User(
                username=username,
                given_name=given_name,
                family_name=family_name,
                password_hash=hash_password(password),
                roles=roles,
            )
            db.add(user)
            db.flush()
            if username == "dev-processor":
                user.area_permissions.append(
                    UserAreaPermission(
                        laboratory_area_id=areas["MICROBIOLOGY"].id,
                        can_preliminary_validate=True,
                        can_final_validate=True,
                    )
                )
            record_audit(
                db,
                actor_user_id=None,
                entity_type="user",
                entity_id=user.id,
                action="DEVELOPMENT_SEED",
                after_data={"username": user.username, "roles": list(role_codes)},
            )
        db.commit()


if __name__ == "__main__":
    seed()
    print("Development seed completed.")
