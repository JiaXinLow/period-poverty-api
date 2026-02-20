from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas import HygieneAccessRead

router = APIRouter(prefix="/v1/hygiene", tags=["Dataset: Hygiene (UK)"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/uk", response_model=list[HygieneAccessRead], summary="Latest UK hygiene indicator(s)")
def hygiene_uk(db: Session = Depends(get_db)):
    # If you ever store multiple years, this returns the latest year by default.
    subq = db.query(models.HygieneAccess.year).order_by(models.HygieneAccess.year.desc()).limit(1).subquery()
    rows = db.query(models.HygieneAccess).filter(models.HygieneAccess.year.in_(subq)).all()
    return rows