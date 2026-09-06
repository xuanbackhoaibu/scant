"""Versioned, non-secret settings consumed directly by application runtime."""
from sqlalchemy import Column, String, Integer, JSON, DateTime
from app.core.database import Base
from app.models.entities import get_utc_now

class AdminConfiguration(Base):
    __tablename__='admin_configuration'
    key=Column(String(40),primary_key=True)
    values_json=Column(JSON,nullable=False,default=dict)
    revision=Column(Integer,nullable=False,default=1)
    updated_at=Column(DateTime(timezone=True),nullable=False,default=get_utc_now,onupdate=get_utc_now)
