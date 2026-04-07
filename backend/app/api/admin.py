from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import get_db_sync
from app.core.deps import get_current_user
from app.core.security import UserResponse
from app.models.models import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserActivateRequest(BaseModel):
    user_id: str


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at
            }
            for u in users
        ],
        "total": total
    }


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return {"message": "User activated", "user_id": user_id}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return {"message": "User deactivated", "user_id": user_id}