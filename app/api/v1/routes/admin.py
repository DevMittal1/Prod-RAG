from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.dependencies import get_current_user
from app.core.security import get_password_hash
from app.db.mongodb import get_db
from app.schemas.admin import (
    AdminResourceListResponse,
    AdminResourceResponse,
    AdminUserCreate,
    AdminUserUpdate,
    EntityCreate,
    EntityUpdate,
    RoleCreate,
    RoleUpdate,
    SessionCreate,
    SessionUpdate,
    TenantCreate,
    TenantUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _object_id(resource_id: str) -> ObjectId:
    try:
        return ObjectId(resource_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid resource ID format")


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _serialize(doc: dict[str, Any]) -> AdminResourceResponse:
    data = dict(doc)
    resource_id = str(data.pop("_id"))
    created_at = data.pop("created_at", None)
    updated_at = data.pop("updated_at", None)
    data.pop("hashed_password", None)
    return AdminResourceResponse(
        id=resource_id,
        created_at=created_at,
        updated_at=updated_at,
        data=data,
    )


async def _create_resource(
    db,
    collection_name: str,
    payload: dict[str, Any],
    unique_filter: dict[str, Any] | None = None,
) -> AdminResourceResponse:
    if unique_filter and await db[collection_name].find_one(unique_filter):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{collection_name.rstrip('s').capitalize()} already exists",
        )

    now = _now()
    doc = {**payload, "created_at": now, "updated_at": now}
    result = await db[collection_name].insert_one(doc)
    created = await db[collection_name].find_one({"_id": result.inserted_id})
    return _serialize(created)


async def _list_resources(
    db,
    collection_name: str,
    skip: int,
    limit: int,
    tenant_id: str | None = None,
) -> AdminResourceListResponse:
    query: dict[str, Any] = {}
    if tenant_id:
        query["tenant_id"] = tenant_id

    cursor = db[collection_name].find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = []
    async for doc in cursor:
        items.append(_serialize(doc))

    total = await db[collection_name].count_documents(query)
    return AdminResourceListResponse(items=items, total=total, skip=skip, limit=limit)


async def _get_resource(db, collection_name: str, resource_id: str) -> AdminResourceResponse:
    doc = await db[collection_name].find_one({"_id": _object_id(resource_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _serialize(doc)


async def _update_resource(
    db,
    collection_name: str,
    resource_id: str,
    payload: dict[str, Any],
    unique_filter: dict[str, Any] | None = None,
) -> AdminResourceResponse:
    if unique_filter:
        existing = await db[collection_name].find_one(unique_filter)
        if existing and str(existing["_id"]) != resource_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{collection_name.rstrip('s').capitalize()} already exists",
            )

    update = _drop_none(payload)
    update["updated_at"] = _now()
    result = await db[collection_name].update_one(
        {"_id": _object_id(resource_id)},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return await _get_resource(db, collection_name, resource_id)


async def _delete_resource(db, collection_name: str, resource_id: str) -> dict[str, str]:
    result = await db[collection_name].delete_one({"_id": _object_id(resource_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"status": "deleted", "id": resource_id}


@router.post("/tenants", response_model=AdminResourceResponse, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _create_resource(
        db,
        "tenants",
        payload.model_dump(),
        unique_filter={"slug": payload.slug},
    )


@router.get("/tenants", response_model=AdminResourceListResponse)
async def list_tenants(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "tenants", skip, limit)


@router.get("/tenants/{tenant_id}", response_model=AdminResourceResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "tenants", tenant_id)


@router.patch("/tenants/{tenant_id}", response_model=AdminResourceResponse)
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    unique_filter = {"slug": data["slug"]} if "slug" in data else None
    return await _update_resource(db, "tenants", tenant_id, data, unique_filter)


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "tenants", tenant_id)


@router.post("/departments", response_model=AdminResourceResponse, status_code=201)
async def create_department(
    payload: EntityCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _create_resource(db, "departments", payload.model_dump())


@router.get("/departments", response_model=AdminResourceListResponse)
async def list_departments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    tenant_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "departments", skip, limit, tenant_id)


@router.get("/departments/{department_id}", response_model=AdminResourceResponse)
async def get_department(
    department_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "departments", department_id)


@router.patch("/departments/{department_id}", response_model=AdminResourceResponse)
async def update_department(
    department_id: str,
    payload: EntityUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _update_resource(
        db,
        "departments",
        department_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "departments", department_id)


@router.post("/tags", response_model=AdminResourceResponse, status_code=201)
async def create_tag(
    payload: EntityCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _create_resource(db, "tags", payload.model_dump())


@router.get("/tags", response_model=AdminResourceListResponse)
async def list_tags(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    tenant_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "tags", skip, limit, tenant_id)


@router.get("/tags/{tag_id}", response_model=AdminResourceResponse)
async def get_tag(
    tag_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "tags", tag_id)


@router.patch("/tags/{tag_id}", response_model=AdminResourceResponse)
async def update_tag(
    tag_id: str,
    payload: EntityUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _update_resource(db, "tags", tag_id, payload.model_dump(exclude_unset=True))


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "tags", tag_id)


@router.post("/roles", response_model=AdminResourceResponse, status_code=201)
async def create_role(
    payload: RoleCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _create_resource(db, "roles", payload.model_dump())


@router.get("/roles", response_model=AdminResourceListResponse)
async def list_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    tenant_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "roles", skip, limit, tenant_id)


@router.get("/roles/{role_id}", response_model=AdminResourceResponse)
async def get_role(
    role_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "roles", role_id)


@router.patch("/roles/{role_id}", response_model=AdminResourceResponse)
async def update_role(
    role_id: str,
    payload: RoleUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _update_resource(db, "roles", role_id, payload.model_dump(exclude_unset=True))


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "roles", role_id)


@router.post("/sessions", response_model=AdminResourceResponse, status_code=201)
async def create_session(
    payload: SessionCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _create_resource(
        db,
        "sessions",
        payload.model_dump(),
        unique_filter={"session_id": payload.session_id},
    )


@router.get("/sessions", response_model=AdminResourceListResponse)
async def list_sessions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    tenant_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "sessions", skip, limit, tenant_id)


@router.get("/sessions/{session_resource_id}", response_model=AdminResourceResponse)
async def get_session(
    session_resource_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "sessions", session_resource_id)


@router.patch("/sessions/{session_resource_id}", response_model=AdminResourceResponse)
async def update_session(
    session_resource_id: str,
    payload: SessionUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _update_resource(
        db,
        "sessions",
        session_resource_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete("/sessions/{session_resource_id}")
async def delete_session(
    session_resource_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "sessions", session_resource_id)


@router.post("/users", response_model=AdminResourceResponse, status_code=201)
async def create_user(
    payload: AdminUserCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    data = payload.model_dump()
    password = data.pop("password")
    data["hashed_password"] = get_password_hash(password)
    return await _create_resource(db, "users", data, unique_filter={"email": payload.email})


@router.get("/users", response_model=AdminResourceListResponse)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    tenant_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _list_resources(db, "users", skip, limit, tenant_id)


@router.get("/users/{user_id}", response_model=AdminResourceResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _get_resource(db, "users", user_id)


@router.patch("/users/{user_id}", response_model=AdminResourceResponse)
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        password = data.pop("password")
        if password:
            data["hashed_password"] = get_password_hash(password)
    unique_filter = {"email": data["email"]} if "email" in data else None
    return await _update_resource(db, "users", user_id, data, unique_filter)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await _delete_resource(db, "users", user_id)
