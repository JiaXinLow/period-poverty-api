from fastapi import FastAPI
from app.database import Base, engine
from app.routers import basket, price_index, pip, hygiene, analytics

app = FastAPI(title="Period Poverty API", version="v1")
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Welcome to the Period Poverty API", "docs": "/docs", "health": "/v1/health"}

@app.get("/v1/health")
def health():
    return {"status": "ok"}

# Routers
app.include_router(basket.router)
app.include_router(price_index.router)
app.include_router(pip.router)
app.include_router(hygiene.router)
app.include_router(analytics.router)