"""
SQLAlchemy ORM models for type safety and migrations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy model for users table."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    conversations = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")
    assets = relationship("AssetModel", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKeyModel", back_populates="user", cascade="all, delete-orphan")
    chart_configs = relationship("ChartConfigurationModel", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_role", "role"),
    )


class ConversationModel(Base):
    """SQLAlchemy model for conversations table."""
    
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    model_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    system_prompt = Column(Text, nullable=True)
    model_parameters = Column(Text, nullable=False, default="{}")
    tags = Column(Text, nullable=False, default="[]")
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_favorite = Column(Boolean, nullable=False, default=False)
    total_tokens = Column(Integer, nullable=False, default=0)
    message_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="conversations")
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    assets = relationship("AssetModel", back_populates="conversation")
    
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_updated_at", "updated_at"),
    )


class MessageModel(Base):
    """SQLAlchemy model for messages table."""
    
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    model_used = Column(String(50), nullable=True)
    generation_time_ms = Column(Float, nullable=True)
    finish_reason = Column(String(50), nullable=True)
    is_edited = Column(Boolean, nullable=False, default=False)
    edited_at = Column(DateTime, nullable=True)
    original_content = Column(Text, nullable=True)
    message_metadata = Column(Text, nullable=False, default="{}")  # RENAMED from 'metadata'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_created_at", "created_at"),
        UniqueConstraint("conversation_id", "sequence_number", name="uq_conversation_sequence"),
    )


class AssetModel(Base):
    """SQLAlchemy model for assets table."""
    
    __tablename__ = "assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    model_used = Column(String(50), nullable=True)
    generation_params = Column(Text, nullable=False, default="{}")
    generation_time_ms = Column(Float, nullable=True)
    tags = Column(Text, nullable=False, default="[]")
    is_favorite = Column(Boolean, nullable=False, default=False)
    is_public = Column(Boolean, nullable=False, default=False)
    view_count = Column(Integer, nullable=False, default=0)
    download_count = Column(Integer, nullable=False, default=0)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    chart_configuration_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="assets")
    conversation = relationship("ConversationModel", back_populates="assets")
    
    __table_args__ = (
        Index("idx_assets_user_id", "user_id"),
        Index("idx_assets_asset_type", "asset_type"),
        Index("idx_assets_created_at", "created_at"),
    )


class ChartConfigurationModel(Base):
    """SQLAlchemy model for chart configurations."""
    
    __tablename__ = "chart_configurations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    chart_type = Column(String(20), nullable=False)
    data_source = Column(Text, nullable=False)
    x_axis_column = Column(String(100), nullable=False)
    y_axis_columns = Column(Text, nullable=False)
    group_by_column = Column(String(100), nullable=True)
    aggregation_function = Column(String(20), nullable=False, default="sum")
    title = Column(String(200), nullable=True)
    x_axis_label = Column(String(100), nullable=True)
    y_axis_label = Column(String(100), nullable=True)
    color_scheme = Column(String(50), default="default")
    theme = Column(String(20), default="dark")
    width = Column(Integer, nullable=False, default=800)
    height = Column(Integer, nullable=False, default=400)
    show_legend = Column(Boolean, nullable=False, default=True)
    show_grid = Column(Boolean, nullable=False, default=True)
    show_tooltips = Column(Boolean, nullable=False, default=True)
    stacked = Column(Boolean, nullable=False, default=False)
    normalized = Column(Boolean, nullable=False, default=False)
    cumulative = Column(Boolean, nullable=False, default=False)
    time_range_start = Column(DateTime, nullable=True)
    time_range_end = Column(DateTime, nullable=True)
    filters = Column(Text, nullable=False, default="{}")
    limit_rows = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=False, default="[]")
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="chart_configs")
    
    __table_args__ = (
        Index("idx_chart_configs_user_id", "user_id"),
    )


class ApiKeyModel(Base):
    """SQLAlchemy model for API keys table."""
    
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    prefix = Column(String(10), nullable=False)
    scopes = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="api_keys")
    
    __table_args__ = (
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_user_id", "user_id"),
    )


class AuditLogModel(Base):
    """SQLAlchemy model for audit logs table."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )