from typing import Optional
from datetime import datetime
import bcrypt

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db_sync
from app.core.security import oauth2_scheme, decode_token, UserResponse
from app.core.settings import get_settings
from app.models.models import User, ApiToken

settings = get_settings()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Depends(oauth2_scheme),
    db = Depends(get_db_sync)
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if authorization and authorization.startswith("sk_live_"):
        return await get_current_user_from_api_token(authorization, db)

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected access token."
            )
    except HTTPException:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive."
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        picture=user.picture,
        is_active=user.is_active,
        is_admin=user.is_admin
    )


async def get_current_user_from_api_token(
    authorization: str,
    db
) -> UserResponse:
    token_value = authorization.replace("Bearer ", "").replace("sk_live_", "sk_live_")
    
    prefix = token_value[:8]
    
    api_token = db.query(ApiToken).filter(
        ApiToken.prefix == prefix,
        ApiToken.is_active == True
    ).first()
    
    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not bcrypt.checkpw(token_value.encode(), api_token.hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_token.last_used_at = datetime.utcnow()
    db.commit()
    
    user = db.query(User).filter(User.id == api_token.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        picture=user.picture,
        is_active=user.is_active,
        is_admin=user.is_admin
    )


async def get_current_admin(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    return current_user