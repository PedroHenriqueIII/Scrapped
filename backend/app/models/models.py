import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class SearchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchType(str, enum.Enum):
    COMPANY = "company"
    PERSON = "person"
    LOCATION = "location"
    VAGUE = "vague"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(512), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Search(Base):
    __tablename__ = "searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    query = Column(Text, nullable=False)
    target_role = Column(String(255), nullable=True)
    status = Column(SQLEnum(SearchStatus), default=SearchStatus.PENDING)
    search_type = Column(SQLEnum(SearchType), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class DecisionMaker(Base):
    __tablename__ = "decision_makers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    sources = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConnectionType(str, enum.Enum):
    LINKEDIN_COOKIE = "linkedin_cookie"


class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(SQLEnum(ConnectionType), nullable=False)
    encrypted_value = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    prefix = Column(String(20), nullable=False)
    hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)