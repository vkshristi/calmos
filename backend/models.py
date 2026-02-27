from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # optional but recommended
    wellness_logs = relationship("WellnessLog", back_populates="user")


class WellnessLog(Base):
    __tablename__ = "wellness_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    log_date = Column(Date, default=date.today, nullable=False)

    mood = Column(Integer, nullable=False)        # 1–5
    sleep_hours = Column(Integer, nullable=False)
    water_intake = Column(Integer, nullable=False)  # glasses
    stress = Column(Integer, nullable=False)      # 1–5
    exercise = Column(Boolean, default=False)

    user = relationship("User", back_populates="wellness_logs")

class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=False)
    flow_rating = Column(Integer, nullable=False)  # 1–5

    user = relationship("User")

class DailyFlow(Base):
    __tablename__ = "daily_flow"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flow_date = Column(Date, nullable=False)

    predicted_score = Column(Integer, nullable=False)
    actual_score = Column(Integer, nullable=True)
    accuracy = Column(Integer, nullable=True)

    user = relationship("User")