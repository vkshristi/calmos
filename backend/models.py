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
