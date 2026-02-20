from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas import PriceIndexRead

router = APIRouter(prefix="/v1/price-index", tags=["Dataset: Price Index"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_month_or_date(s: str) -> datetime:
    """
    Accept 'YYYY-MM' or 'YYYY-MM-DD'; return datetime.date at month start.
    """
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            dt = datetime.strptime(s, fmt)
            if fmt == "%Y-%m":
                # normalize month strings to first day of month
                return datetime(dt.year, dt.month, 1)
            return dt
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM or YYYY-MM-DD.")

@router.get("/", response_model=list[PriceIndexRead], summary="CPI personal care monthly series")
def list_price_index(
    from_: str | None = Query(None, alias="from", description="Start month (YYYY-MM) or date (YYYY-MM-DD)"),
    to: str | None = Query(None, description="End month (YYYY-MM) or date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    q = db.query(models.PriceIndex)
    if from_:
        start = parse_month_or_date(from_).date()
        q = q.filter(models.PriceIndex.date >= start)
    if to:
        end = parse_month_or_date(to).date()
        q = q.filter(models.PriceIndex.date <= end)

    rows = q.order_by(models.PriceIndex.date.asc()).all()
    # Serialize to simple dicts with ISO dates
    return [
        {
            "date": r.date.isoformat(),
            "cpi_index": r.cpi_index,
            "pct_change_mom": r.pct_change_mom,
            "pct_change_yoy": r.pct_change_yoy,
        }
        for r in rows
    ]