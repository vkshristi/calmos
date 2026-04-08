from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from database import engine, SessionLocal
from models import Base, User, WellnessLog, FocusSession
from auth import hash_password, verify_password, create_access_token
from flow_engine import compute_flow_score
from models import Base, User, WellnessLog, FocusSession, DailyFlow
from insights_engine import (
    sleep_vs_flow,
    stress_vs_focus,
    context_switch_penalty,
    burnout_risk,
    generate_insights
)

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

@app.get("/flow/today")
def get_today_flow(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

#    today = date.today()
    today = date(2026, 4, 5)
    print("FLOW DATE:", today)

    # Wellness
    wellness = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date == today
        )
        .first()
    )

    # Focus
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
    avg_flow = (
        sum(s.flow_rating for s in sessions) / len(sessions)
        if sessions else None
    )

    focus_summary = {
        "total_minutes": total_minutes,
        "average_flow": avg_flow
    }

    wellness_data = None

    if wellness:
        wellness_data = {
            "mood": wellness.mood,
            "sleep_hours": wellness.sleep_hours,
            "water_intake": wellness.water_intake,
            "stress": wellness.stress,
            "exercise": wellness.exercise,
        }

    score = compute_flow_score(wellness_data, focus_summary)

    if score is None:
        return {"flow_score": None}

    # Check if already stored
    existing = (
        db.query(DailyFlow)
        .filter(
            DailyFlow.user_id == user.id,
            DailyFlow.flow_date == today
        )
        .first()
    )

    if existing:
        existing.predicted_score = score
    else:
        new_flow = DailyFlow(
            user_id=user.id,
            flow_date=today,
            predicted_score=score
        )
        db.add(new_flow)

    db.commit()

    return {"flow_score": score}

@app.post("/flow/update-actual")
def update_actual_flow(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()

    daily_flow = (
        db.query(DailyFlow)
        .filter(
            DailyFlow.user_id == user.id,
            DailyFlow.flow_date == today
        )
        .first()
    )

    if not daily_flow:
        raise HTTPException(status_code=404, detail="No predicted flow found")

    sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == user.id,
            FocusSession.start_time >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        .all()
    )

    if not sessions:
        raise HTTPException(status_code=400, detail="No focus sessions today")

    avg_flow_rating = sum(s.flow_rating for s in sessions) / len(sessions)

    # Normalize actual to 0–100
    actual_score = round(((avg_flow_rating - 1) / 4) * 100)

    predicted = daily_flow.predicted_score

    accuracy = max(0, 100 - abs(predicted - actual_score))

    daily_flow.actual_score = actual_score
    daily_flow.accuracy = accuracy

    db.commit()

    return {
        "predicted": predicted,
        "actual": actual_score,
        "accuracy": accuracy
    }

@app.get("/flow/accuracy")
def get_flow_accuracy(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    records = (
        db.query(DailyFlow)
        .filter(DailyFlow.user_id == user.id)
        .order_by(DailyFlow.flow_date.desc())
        .all()
    )

    return records

@app.get("/flow/week")
def get_week_flow(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    start_date = date.today() - timedelta(days=7)

    records = (
        db.query(DailyFlow)
        .filter(
            DailyFlow.user_id == user.id,
            DailyFlow.flow_date >= start_date
        )
        .order_by(DailyFlow.flow_date.asc())
        .all()
    )

    if not records:
        return {"records": [], "average_flow": None, "average_accuracy": None}

    avg_flow = sum(r.predicted_score for r in records) / len(records)

    accuracy_values = [r.accuracy for r in records if r.accuracy is not None]
    avg_accuracy = (
        sum(accuracy_values) / len(accuracy_values)
        if accuracy_values else None
    )

    return {
        "records": records,
        "average_flow": round(avg_flow, 2),
        "average_accuracy": round(avg_accuracy, 2) if avg_accuracy else None
    }

@app.get("/insights/today")
def get_insights(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Last 7 days data
    start_date = date.today() - timedelta(days=7)

    flows = (
        db.query(DailyFlow)
        .filter(
            DailyFlow.user_id == user.id,
            DailyFlow.flow_date >= start_date
        )
        .all()
    )

    wellness_logs = (
        db.query(WellnessLog)
        .filter(
            WellnessLog.user_id == user.id,
            WellnessLog.log_date >= start_date
        )
        .all()
    )

    focus_sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == user.id,
            FocusSession.start_time >= datetime.utcnow() - timedelta(days=7)
        )
        .all()
    )

    # Build combined records
    records = []

    for flow in flows:
        date_key = flow.flow_date

        w = next((x for x in wellness_logs if x.log_date == date_key), None)

        sessions = [
            s for s in focus_sessions
            if s.start_time.date() == date_key
        ]

        if not sessions:
            continue

        total_focus = sum(s.duration_minutes for s in sessions)
        avg_flow = sum(s.flow_rating for s in sessions) / len(sessions)

        records.append({
            "sleep": w.sleep_hours if w else None,
            "stress": w.stress if w else None,
            "flow": avg_flow,
            "focus": total_focus,
            "sessions": len(sessions),
            "avg_flow": avg_flow
        })

    if not records:
        return {"insights": []}

    print("FINAL RECORDS:", records)
    sleep_corr = sleep_vs_flow(records)
    stress_corr = stress_vs_focus(records)
    switch_pen = context_switch_penalty(records)

    latest = records[-1]

    burnout = burnout_risk(latest)

    insights = generate_insights(
        sleep_corr,
        stress_corr,
        switch_pen,
        burnout
    )

    return {
        "insights": insights,
        "burnout_risk": burnout,
        "metrics": {
            "sleep_vs_flow": sleep_corr,
            "stress_vs_focus": stress_corr,
            "context_switch_penalty": switch_pen
        }
    }