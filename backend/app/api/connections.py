from datetime import datetime, timedelta
from typing import Optional
import secrets
import bcrypt
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.database import get_db_sync
from app.core.deps import get_current_user
from app.core.security import UserResponse
from app.core.encryption import encrypt_value, decrypt_value
from app.models.models import Connection, ConnectionType, ApiToken

router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.get("")
async def list_connections(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    connections = db.query(Connection).filter(
        Connection.user_id == UUID(current_user.id)
    ).all()
    
    result = []
    for conn in connections:
        days_remaining = None
        if conn.expires_at:
            days_remaining = (conn.expires_at - datetime.utcnow()).days
        
        result.append({
            "id": str(conn.id),
            "type": conn.type.value,
            "expires_at": conn.expires_at.isoformat() if conn.expires_at else None,
            "last_validated_at": conn.last_validated_at.isoformat() if conn.last_validated_at else None,
            "days_remaining": days_remaining,
            "created_at": conn.created_at.isoformat()
        })
    
    api_token = db.query(ApiToken).filter(
        ApiToken.user_id == UUID(current_user.id),
        ApiToken.is_active == True
    ).first()
    
    api_token_data = None
    if api_token:
        api_token_data = {
            "prefix": api_token.prefix,
            "created_at": api_token.created_at.isoformat(),
            "last_used_at": api_token.last_used_at.isoformat() if api_token.last_used_at else None
        }
    
    return {"connections": result, "api_token": api_token_data}


@router.post("/linkedin")
async def save_linkedin_cookie(
    li_at: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    existing = db.query(Connection).filter(
        Connection.user_id == UUID(current_user.id),
        Connection.type == ConnectionType.LINKEDIN_COOKIE
    ).first()
    
    if existing:
        existing.encrypted_value = encrypt_value(li_at)
        existing.expires_at = datetime.utcnow() + timedelta(days=30)
        existing.last_validated_at = datetime.utcnow()
        db.commit()
    else:
        connection = Connection(
            user_id=UUID(current_user.id),
            type=ConnectionType.LINKEDIN_COOKIE,
            encrypted_value=encrypt_value(li_at),
            expires_at=datetime.utcnow() + timedelta(days=30),
            last_validated_at=datetime.utcnow()
        )
        db.add(connection)
        db.commit()
    
    return {"message": "Cookie LinkedIn salvo com sucesso"}


@router.delete("/linkedin")
async def delete_linkedin_cookie(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    connection = db.query(Connection).filter(
        Connection.user_id == UUID(current_user.id),
        Connection.type == ConnectionType.LINKEDIN_COOKIE
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Nenhum cookie LinkedIn encontrado")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Cookie LinkedIn removido"}


@router.post("/linkedin/validate")
async def validate_linkedin_session(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    connection = db.query(Connection).filter(
        Connection.user_id == UUID(current_user.id),
        Connection.type == ConnectionType.LINKEDIN_COOKIE
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Nenhum cookie LinkedIn encontrado")
    
    li_at = decrypt_value(connection.encrypted_value)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.linkedin.com/feed/",
                cookies={"li_at": li_at},
                timeout=10.0
            )
            
            is_valid = response.status_code == 200 and (
                "loggedIn" in response.text or 
                "miniprofile" in response.text or
                'nav-name' in response.text
            )
    except Exception:
        is_valid = False
    
    connection.last_validated_at = datetime.utcnow()
    db.commit()
    
    days_remaining = (connection.expires_at - datetime.utcnow()).days
    
    return {
        "valid": is_valid,
        "expires_at": connection.expires_at.isoformat(),
        "days_remaining": days_remaining
    }


@router.get("/api-token")
async def get_api_token_metadata(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    token = db.query(ApiToken).filter(
        ApiToken.user_id == UUID(current_user.id),
        ApiToken.is_active == True
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Nenhum token de API encontrado")
    
    return {
        "prefix": token.prefix,
        "created_at": token.created_at.isoformat(),
        "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None
    }


@router.post("/api-token/generate")
async def generate_api_token(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    existing = db.query(ApiToken).filter(
        ApiToken.user_id == UUID(current_user.id),
        ApiToken.is_active == True
    ).first()
    
    if existing:
        existing.is_active = False
        db.commit()
    
    token_value = "sk_live_" + secrets.token_urlsafe(32)
    prefix = "sk_live_" + token_value[:4]
    hash = bcrypt.hashpw(token_value.encode(), bcrypt.gensalt()).decode()
    
    api_token = ApiToken(
        user_id=UUID(current_user.id),
        prefix=prefix,
        hash=hash
    )
    db.add(api_token)
    db.commit()
    
    return {"token": token_value}


@router.delete("/api-token")
async def revoke_api_token(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    token = db.query(ApiToken).filter(
        ApiToken.user_id == UUID(current_user.id),
        ApiToken.is_active == True
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Nenhum token de API encontrado")
    
    token.is_active = False
    db.commit()
    
    return {"message": "Token de API revogado"}
