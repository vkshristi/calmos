from fastapi import FastAPI
from database import engine

app = FastAPI()

@app.get("/")
def root():
    try:
        connection = engine.connect()
        connection.close()
        return {"status": "CalmOS backend + database connected"}
    except Exception as e:
        return {"error": str(e)}
