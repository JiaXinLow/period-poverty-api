# app/routers/analytics.py

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models
from app.schemas import (
    InflationTrendResponse, InflationTrendPoint,
    CostEstimateRequest, CostEstimateResponse, BasketLine,
    CostBurdenResponse, SeverityScoreResponse
)

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


# -------------------------------
# DB session dependency
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------
# Helpers
# -------------------------------
def parse_month_or_date(s: str) -> datetime:
    """
    Accept 'YYYY-MM' or 'YYYY-MM-DD'; normalize to the first day of the month
    for 'YYYY-MM'. Raises 400 on invalid input.
    """
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            dt = datetime.strptime(s, fmt)
            if fmt == "%Y-%m":
                return datetime(dt.year, dt.month, 1)
            return dt
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM or YYYY-MM-DD.")


def _sum_basket_lines(lines: List[BasketLine]) -> float:
    return float(sum(li.unit_price * li.units_per_month for li in lines))


# -------------------------------
# 1) Inflation trend
# -------------------------------
@router.get("/inflation-trend", response_model=InflationTrendResponse, summary="CPI personal care trend")
def inflation_trend(
    from_: str | None = Query(None, alias="from", description="YYYY-MM or YYYY-MM-DD"),
    to: str | None = Query(None, description="YYYY-MM or YYYY-MM-DD"),
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
    points = [
        InflationTrendPoint(
            date=r.date.isoformat(),
            cpi_index=r.cpi_index,
            pct_change_yoy=r.pct_change_yoy,
        )
        for r in rows
    ]
    return InflationTrendResponse(from_=from_, to=to, points=points)


# -------------------------------
# 2) Cost estimate
# -------------------------------
@router.post(
    "/cost-estimate",
    response_model=CostEstimateResponse,
    summary="Estimate monthly/annual basket cost",
)
def cost_estimate(
    payload: CostEstimateRequest = Body(
        ...,
        examples={
            "use_db_basket": {
                "summary": "Use existing DB basket items",
                "value": {"apply_yoy_cpi": False}
            },
            "custom_basket": {
                "summary": "Provide a custom basket",
                "value": {
                    "apply_yoy_cpi": True,
                    "lines": [
                        {"name": "pads pack", "unit_price": 2.5, "units_per_month": 2, "currency": "GBP"}
                    ]
                }
            }
        }
    ),
    db: Session = Depends(get_db)
):
    """
    Computes:
      - monthly_cost = sum(unit_price * units_per_month)
      - annual_cost  = monthly_cost * 12

    If `apply_yoy_cpi=True`, the monthly cost is multiplied by (1 + latest_yoy/100)
    using the latest record in the PriceIndex table.
    """
    # 1) Decide where lines come from: request body or DB
    if payload.lines and len(payload.lines) > 0:
        lines = payload.lines
    else:
        items = db.query(models.BasketItem).all()
        lines = [
            BasketLine(
                name=i.name,
                unit_price=i.unit_price,
                units_per_month=i.units_per_month,
                currency=i.currency,
                notes=i.notes,
            )
            for i in items
        ]

    if not lines:
        raise HTTPException(status_code=400, detail="No basket items provided or found in DB.")

    # 2) Base monthly cost (before CPI uplift)
    monthly = _sum_basket_lines(lines)

    # 3) Optional: apply latest YoY CPI (personal care) uplift
    if payload.apply_yoy_cpi:
        latest = db.query(models.PriceIndex).order_by(models.PriceIndex.date.desc()).first()
        if latest is None:
            raise HTTPException(status_code=400, detail="No CPI data available to apply YoY inflation.")
        yoy = latest.pct_change_yoy or 0.0
        monthly = monthly * (1.0 + yoy / 100.0)

    annual = monthly * 12.0

    # 4) Respond with rounded figures and echo of used lines
    return CostEstimateResponse(
        monthly_cost=round(monthly, 2),
        annual_cost=round(annual, 2),
        used_lines=lines,
    )


# -------------------------------
# 3) Cost burden
# -------------------------------
@router.get("/cost-burden", response_model=CostBurdenResponse, summary="Annual cost burden vs PIP welfare")
def cost_burden(
    year: int = Query(..., ge=1900, le=2100),
    percentile: int = Query(..., ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Get annual cost from DB basket (no CPI scenario here; keep deterministic)
    items = db.query(models.BasketItem).all()
    if not items:
        raise HTTPException(status_code=400, detail="No basket items in DB. Create items first.")
    annual_cost = sum(i.unit_price * i.units_per_month for i in items) * 12.0

    # Get avg_welfare (daily PPP) for requested year/percentile
    rec = db.query(models.IncomePoverty).filter(
        models.IncomePoverty.year == year,
        models.IncomePoverty.percentile == percentile,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"No PIP data for year={year}, percentile={percentile}")

    avg_annual = rec.avg_welfare * 365.0  # convert daily PPP to annual
    burden_ratio = float(annual_cost) / float(avg_annual) if avg_annual > 0 else 0.0

    return CostBurdenResponse(
        year=year,
        percentile=percentile,
        annual_cost=round(annual_cost, 2),
        avg_welfare_annual_ppp=round(avg_annual, 2),
        burden_ratio=round(burden_ratio, 4),
    )


# -------------------------------
# 4) Hygiene severity score
# -------------------------------
@router.get("/severity-score", response_model=SeverityScoreResponse, summary="Combine hygiene + affordability into a severity score")
def severity_score(
    year: int = Query(2018, ge=1900, le=2100, description="Hygiene indicator year; default 2018 for UK"),
    percentile: int = Query(20, ge=1, le=100, description="Income percentile for affordability comparison"),
    db: Session = Depends(get_db)
):
    # Annual cost from basket
    items = db.query(models.BasketItem).all()
    if not items:
        raise HTTPException(status_code=400, detail="No basket items in DB. Create items first.")
    annual_cost = sum(i.unit_price * i.units_per_month for i in items) * 12.0

    # PIP welfare (annual)
    rec = db.query(models.IncomePoverty).filter(
        models.IncomePoverty.year == year,
        models.IncomePoverty.percentile == percentile,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"No PIP data for year={year}, percentile={percentile}")
    avg_annual = rec.avg_welfare * 365.0
    burden_ratio = float(annual_cost) / float(avg_annual) if avg_annual > 0 else 0.0

    # Hygiene (latest year by default; fallback to requested year if multiple)
    latest_year = db.query(func.max(models.HygieneAccess.year)).scalar()
    hrow = db.query(models.HygieneAccess).filter(models.HygieneAccess.year == (latest_year or year)).first()
    if not hrow:
        raise HTTPException(status_code=404, detail="No hygiene data available")

    hygiene_value = hrow.value  # e.g., 99.7 (%)
    hygiene_severity = 1.0 - (hygiene_value / 100.0)  # lower access => higher severity

    # Simple composite (you can refine and justify in your report)
    # Example weighting: 70% burden (affordability), 30% hygiene severity
    combined = 0.7 * burden_ratio + 0.3 * hygiene_severity

    return SeverityScoreResponse(
        year=rec.year,
        annual_cost=round(annual_cost, 2),
        avg_welfare_annual_ppp=round(avg_annual, 2),
        burden_ratio=round(burden_ratio, 4),
        hygiene_value_pct=round(hygiene_value, 1),
        hygiene_severity=round(hygiene_severity, 4),
        combined_severity=round(combined, 4),
    )