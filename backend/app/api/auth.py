import secrets
import redis
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, UserResponse
from app.core.settings import get_settings
from app.core.deps import get_current_user
from app.models.models import User

settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/google")
async def google_auth(request: Request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state if hasattr(request, "session") else None

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"state={state}"
    )
    return {"authorization_url": google_auth_url}


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None, db: Session = Depends(get_db)):
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()

    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email, name=name, picture=picture, is_active=False)
        db.add(user)
        db.commit()
        db.refresh(user)
        is_active = False
    else:
        is_active = bool(user.is_active)

    if is_active == False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized. Contact admin."
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    blacklist_key = f"blacklist:{refresh_token}"
    if redis_client.exists(blacklist_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token."
            )

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        user_is_active = bool(user.is_active) if user is not None else False
        if user is None or user_is_active == False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        new_access_token = create_access_token(str(user.id))
        return {"access_token": new_access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(refresh_token: Optional[str] = None):
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") == "refresh":
                exp = payload.get("exp")
                iat = payload.get("iat")
                if exp is not None and iat is not None:
                    ttl = exp - iat
                    blacklist_key = f"blacklist:{refresh_token}"
                    redis_client.setex(blacklist_key, ttl, "1")
        except Exception:
            pass

    return {"message": "Logged out successfully"}