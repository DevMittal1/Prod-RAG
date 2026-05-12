from typing import Any

from pydantic import BaseModel, EmailStr, Field


class EntityCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] | None = None


class TenantCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1)
    description: str | None = None
    metadata: dict[str, Any] | None = None


class RoleCreate(EntityCreate):
    permissions: list[str] = Field(default_factory=list)


class RoleUpdate(EntityUpdate):
    permissions: list[str] | None = None


class SessionCreate(BaseModel):
    session_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    tenant_id: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    user_id: str | None = Field(default=None, min_length=1)
    tenant_id: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)
    full_name: str | None = None
    tenant_id: str | None = None
    roles: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, max_length=72)
    full_name: str | None = None
    tenant_id: str | None = None
    roles: list[str] | None = None
    metadata: dict[str, Any] | None = None


class AdminResourceResponse(BaseModel):
    id: str
    created_at: str | None = None
    updated_at: str | None = None
    data: dict[str, Any]


class AdminResourceListResponse(BaseModel):
    items: list[AdminResourceResponse]
    total: int
    skip: int
    limit: int
