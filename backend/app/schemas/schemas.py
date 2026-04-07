from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class UserBase(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SearchCreate(BaseModel):
    query: str
    target_role: Optional[str] = None


class SearchBatchCreate(BaseModel):
    queries: List[str]
    target_role: str


class DecisionMakerResponse(BaseModel):
    id: UUID
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    sources: Optional[List[str]] = None
    confidence_score: float

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    id: UUID
    user_id: UUID
    query: str
    target_role: Optional[str] = None
    status: str
    search_type: Optional[str] = None
    results: Optional[List[DecisionMakerResponse]] = []
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchStatusResponse(BaseModel):
    id: UUID
    status: str
    search_type: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SearchListResponse(BaseModel):
    searches: List[SearchStatusResponse]
    total: int