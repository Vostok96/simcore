from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AreaPermissionInput(BaseModel):
    laboratory_area_id: str
    can_preliminary_validate: bool = False
    can_final_validate: bool = False


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    given_name: str = Field(min_length=1, max_length=120)
    family_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=256)
    role_codes: list[str] = Field(min_length=1)
    area_permissions: list[AreaPermissionInput] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    role_codes: list[str] = Field(min_length=1)


class LaboratoryAreaCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    section: str = Field(default="MICROBIOLOGY", min_length=2, max_length=80)


class AreaPermissionUpdate(BaseModel):
    area_permissions: list[AreaPermissionInput]


class UserResponse(BaseModel):
    id: str
    username: str
    given_name: str
    family_name: str
    is_active: bool
    roles: list[str]


class AuditEventResponse(BaseModel):
    id: str
    actor_user_id: str | None
    entity_type: str
    entity_id: str | None
    action: str
    occurred_at: datetime
    reason: str | None
