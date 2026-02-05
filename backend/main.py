from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, User
from auth import hash_password, verify_password, create_access_token

app = FastAPI()

# DEV ONLY — OK for now
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/signup")
def signup(email: str, password: str):
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        user = User(
            email=email,
            password_hash=hash_password(password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {"message": "User created successfully"}

    except:
        db.rollback()
        raise

    finally:
        db.close()


@app.post("/login")
def login(email: str, password: str):
    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        token = create_access_token({"sub": user.email})

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "CalmOS auth backend running"}
