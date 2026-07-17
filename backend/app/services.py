from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Role, User


ROLE_SEEDS = {
    "ADMIN": "Administrator",
    "PROCESS_ADMIN": "Process administrator",
    "PROCESSOR": "Laboratory processor",
    "ENTRY": "Order entry",
    "CONSULTANT": "Consultation user",
    "COLLECTOR": "Specimen collector",
    "CLINICIAN": "Clinician consultation",
}


def record_audit(
    db: Session,
    *,
    actor_user_id: str | None,
    entity_type: str,
    entity_id: str | None,
    action: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    reason: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_data=before_data,
        after_data=after_data,
        reason=reason,
    )
    db.add(event)
    return event


def get_roles(db: Session, role_codes: list[str]) -> list[Role]:
    requested = {code.upper() for code in role_codes}
    roles = list(db.scalars(select(Role).where(Role.code.in_(requested))))
    found = {role.code for role in roles}
    missing = requested - found
    if missing:
        raise ValueError(f"Unknown roles: {', '.join(sorted(missing))}")
    return roles


def bootstrap_security_data(db: Session, username: str | None, password: str | None, given_name: str, family_name: str, password_hasher) -> None:
    for code, name in ROLE_SEEDS.items():
        if not db.scalar(select(Role).where(Role.code == code)):
            db.add(Role(code=code, name=name))
    db.flush()

    if username and password and not db.scalar(select(User).where(User.username == username)):
        admin_role = db.scalar(select(Role).where(Role.code == "ADMIN"))
        user = User(
            username=username,
            given_name=given_name,
            family_name=family_name,
            password_hash=password_hasher(password),
            roles=[admin_role],
        )
        db.add(user)
        db.flush()
        record_audit(
            db,
            actor_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            action="BOOTSTRAP_ADMIN_CREATED",
            after_data={"username": user.username, "roles": ["ADMIN"]},
        )
    db.commit()
