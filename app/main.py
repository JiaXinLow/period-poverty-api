from fastapi import FastAPI
from .database import Base, engine

app = FastAPI(title="Period Poverty API", version="v1")

# Create tables at startup (idempotent)
Base.metadata.create_all(bind=engine)

@app.get("/v1/health")
def health():
    return {"status": "ok"}