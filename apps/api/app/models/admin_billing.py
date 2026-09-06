"""Persistent checkout evidence and activated plan records (no payment credentials)."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.core.database import Base
from app.models.entities import generate_uuid, get_utc_now


class Payment(Base):
    __tablename__ = "billing_payments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    provider = Column(String(30), nullable=False)
    provider_session_id = Column(String(100), nullable=False, unique=True)
    provider_transaction_id = Column(String(150), nullable=True, unique=True)
    order_code = Column(String(30), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now)
    paid_at = Column(DateTime(timezone=True))


class Subscription(Base):
    __tablename__ = "billing_subscriptions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="active")
    provider = Column(String(30), nullable=False)
    payment_id = Column(String(36), ForeignKey("billing_payments.id"), nullable=True, unique=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now)
    ended_at = Column(DateTime(timezone=True))
