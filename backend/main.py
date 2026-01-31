from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, User

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "CalmOS backend running with users table"}
