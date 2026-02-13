from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from database import engine, SessionLocal
from models import Base, User, WellnessLog, FocusSession
from auth import hash_password, verify_password, create_access_token

app = FastAPI()

# ✅ CORS — REQUIRED for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DEV ONLY — OK for now
Base.metadata.create_all(bind=engine)


# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Request Schemas ----------
class AuthRequest(BaseModel):
    email: str
    password: str


# ---------- Auth Routes ----------
@app.post("/signup")
def signup(data: AuthRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}


@app.post("/login")
def login(data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})

    return {"access_token": token, "token_type": "bearer"}


@app.get("/")
def root():
    return {"status": "CalmOS auth backend running"}


# ---------- Wellness Routes ----------
@app.post("/wellness")
def create_wellness(
    user_email: str,
    mood: int,
    sleep_hours: int,
    water_intake: int,
    stress: int,
    exercise: bool,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()

    existing = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date == today,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Wellness already logged today")

    log = WellnessLog(
        user_id=user.id,
        mood=mood,
        sleep_hours=sleep_hours,
        water_intake=water_intake,
        stress=stress,
        exercise=exercise,
    )

    db.add(log)
    db.commit()

    return {"message": "Wellness log created"}


@app.get("/wellness/today")
def get_today_wellness(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date == date.today(),
        )
        .first()
    )

    if not log:
        return None

    return {
        "date": log.log_date,
        "mood": log.mood,
        "sleep_hours": log.sleep_hours,
        "water_intake": log.water_intake,
        "stress": log.stress,
        "exercise": log.exercise,
    }


@app.get("/wellness/week")
def get_week_wellness(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    start_date = date.today() - timedelta(days=7)

    logs = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date >= start_date,
        )
        .order_by(WellnessLog.log_date.desc())
        .all()
    )

    return [
        {
            "date": log.log_date,
            "mood": log.mood,
            "sleep_hours": log.sleep_hours,
            "water_intake": log.water_intake,
            "stress": log.stress,
            "exercise": log.exercise,
        }
        for log in logs
    ]


from pydantic import BaseModel

class FocusRequest(BaseModel):
    user_email: str
    duration_minutes: int
    flow_rating: int

@app.post("/focus")
def create_focus(data: FocusRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = FocusSession(
        user_id=user.id,
        duration_minutes=data.duration_minutes,
        flow_rating=data.flow_rating,
        start_time=datetime.utcnow(),  # ensure timestamp exists
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {"message": "Focus session saved"}


@app.get("/focus/today")
def get_today_focus(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == user.id,
            FocusSession.start_time >= today_start
        )
        .all()
    )

    total_minutes = sum(s.duration_minutes for s in sessions)

    return {
        "total_minutes": total_minutes,
        "sessions": [
            {
                "id": s.id,
                "duration_minutes": s.duration_minutes,
                "flow_rating": s.flow_rating,
                "start_time": s.start_time,
            }
            for s in sessions
        ],
    }


@app.get("/summary/today")
def get_daily_summary(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ---- Wellness ----
    today = date.today()
    wellness = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date == today
        )
        .first()
    )

    # ---- Focus ----
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    focus_sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == user.id,
            FocusSession.start_time >= today_start
        )
        .all()
    )

    total_focus_minutes = sum(s.duration_minutes for s in focus_sessions)

    avg_flow = (
        sum(s.flow_rating for s in focus_sessions) / len(focus_sessions)
        if focus_sessions else None
    )

    return {
        "wellness": wellness,
        "focus": {
            "total_minutes": total_focus_minutes,
            "average_flow": avg_flow,
            "session_count": len(focus_sessions)
        }
    }
