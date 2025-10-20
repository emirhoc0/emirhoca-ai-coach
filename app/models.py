from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from .database import Base

# Utility column factory

def now_utc():
    return datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="free")

    onboarding = relationship("Onboarding", back_populates="user", uselist=False)
    programs = relationship("Program", back_populates="user")

class Onboarding(Base):
    __tablename__ = "onboarding"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    goal: Mapped[str | None] = mapped_column(String(50))
    sex: Mapped[str | None] = mapped_column(String(10))
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    days_per_week: Mapped[int | None] = mapped_column(Integer)
    session_minutes: Mapped[int | None] = mapped_column(Integer)
    experience: Mapped[str | None] = mapped_column(String(50))
    equipment: Mapped[str | None] = mapped_column(Text)  # comma/JSON list
    injuries: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="onboarding")

class Program(Base):
    __tablename__ = "program"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    split: Mapped[str] = mapped_column(String(50))
    plan_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    user = relationship("User", back_populates="programs")

class SetLog(Base):
    __tablename__ = "set_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    exercise: Mapped[str] = mapped_column(String(255))
    sets: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    rpe: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)

class Biometrics(Base):
    __tablename__ = "biometrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)

class Adherence(Base):
    __tablename__ = "adherence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    train_pct: Mapped[float | None] = mapped_column(Float)
    nutrition_pct: Mapped[float | None] = mapped_column(Float)
    sleep_avg: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)

class AdjustmentEvent(Base):
    __tablename__ = "adjustment_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    payload_json: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user/assistant/system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(50))  # stripe/shopier
    status: Mapped[str] = mapped_column(String(50))    # paid/pending/failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)