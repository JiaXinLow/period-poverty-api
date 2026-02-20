from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas import IncomePovertyRead

router = APIRouter(prefix="/v1/pip", tags=["Dataset: PIP (UK)"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/uk/{year}", response_model=list[IncomePovertyRead], summary="UK percentiles for a year (daily PPP)")
def pip_uk_year(
    year: int = Path(..., ge=1900, le=2100),
    db: Session = Depends(get_db)
):
    q = db.query(models.IncomePoverty).filter(models.IncomePoverty.year == year).order_by(models.IncomePoverty.percentile.asc())
    rows = q.all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No UK national percentiles found for year={year}")
    # Return as-is; schema has from_attributes to serialize ORM
    return rows