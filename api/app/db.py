"""Database layer: shared async engine + ORM models.

This module is the single source of the connection pool (avoids the circular
imports we hit earlier). Import `get_session` anywhere; never create a second
engine.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _namespace() -> str:
    """An opaque, collision-resistant isolation key (128 bits of entropy).

    Deliberately carries NO matter name, person name, or any other semantic /
    PII content — the human-readable label lives in `Member.name`, not here. The
    namespace is resolved server-side from the principal record and is never
    supplied by a client, so it doesn't need to be secret; making it opaque is a
    hardening measure so the store leaks nothing if inspected.
    """
    return "ns_" + secrets.token_hex(16)


class Base(DeclarativeBase):
    pass


# ── shared engine / sessionmaker ────────────────────────────────────────────
_settings = get_settings()
engine = create_async_engine(_settings.postgres_dsn, pool_pre_ping=True, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if absent. Hackathon-simple; swap for Alembic in prod."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── models (mirror TDD Section 4, generalized member->principal-ready) ───────
class Household(Base):
    __tablename__ = "households"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    members: Mapped[list["Member"]] = relationship(back_populates="household")


class Member(Base):
    __tablename__ = "members"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("households.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    persona_key: Mapped[str] = mapped_column(String(64), nullable=False)
    # the isolation key — every memory and every vector carries this
    memory_namespace: Mapped[str] = mapped_column(Text, nullable=False, unique=True, default=_namespace)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    household: Mapped[Household] = relationship(back_populates="members")
    # role is free-form so one model serves any use case:
    # a family member, a legal matter, a SaaS tenant, an agent, etc.


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    __table_args__ = (
        CheckConstraint("role IN ('user','assistant','system')", name="ck_message_role"),
    )


class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)  # denormalized isolation key
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    salience: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("memories.id"), nullable=True)
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    qdrant_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, default=_uuid)
    __table_args__ = (
        CheckConstraint("kind IN ('fact','preference','event','task','relationship')", name="ck_memory_kind"),
        CheckConstraint("status IN ('active','superseded','expired')", name="ck_memory_status"),
        Index("idx_memories_member_active", "member_id", "status"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    member_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ProposedAction(Base):
    __tablename__ = "proposed_actions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="ck_action_status"),
    )
