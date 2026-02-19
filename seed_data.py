import pandas as pd
from datetime import datetime
from app.database import Base, engine, SessionLocal
from app import models

def seed_price_index(db: SessionLocal):
    df = pd.read_csv("data/processed/cpi_personal_care.csv", parse_dates=["date"])
    # Normalize columns that may be missing
    for col in ["pct_change_mom", "pct_change_yoy"]:
        if col not in df.columns:
            df[col] = None

    for _, r in df.iterrows():
        date_value = r["date"].date() if isinstance(r["date"], pd.Timestamp) else datetime.strptime(str(r["date"]), "%Y-%m-%d").date()
        row = models.PriceIndex(
            date=date_value,
            cpi_index=float(r["cpi_index"]),
            pct_change_mom=None if pd.isna(r.get("pct_change_mom")) else float(r["pct_change_mom"]),
            pct_change_yoy=None if pd.isna(r.get("pct_change_yoy")) else float(r["pct_change_yoy"]),
        )
        # upsert-like behavior via merge (safe enough for seeding)
        db.merge(row)

def seed_income_poverty(db: SessionLocal):
    df = pd.read_csv("data/processed/pip_uk_percentiles.csv")
    # Your final file has: year, percentile, avg_welfare_daily_ppp, avg_welfare_annual_ppp, welfare_type
    # We’ll store the DAILY PPP in avg_welfare to keep model simple; annual can be derived as needed.
    daily_col = "avg_welfare_daily_ppp" if "avg_welfare_daily_ppp" in df.columns else "avg_welfare"
    for _, r in df.iterrows():
        row = models.IncomePoverty(
            year=int(r["year"]),
            percentile=int(r["percentile"]),
            avg_welfare=float(r[daily_col]),
            welfare_type=str(r.get("welfare_type")) if not pd.isna(r.get("welfare_type")) else None
        )
        db.merge(row)

def seed_hygiene_access(db: SessionLocal):
    df = pd.read_csv("data/processed/hygiene_uk.csv")
    # Expect: country, year, indicator, value
    for _, r in df.iterrows():
        row = models.HygieneAccess(
            country=str(r["country"]),
            year=int(r["year"]),
            indicator=str(r["indicator"]),
            value=float(r["value"])
        )
        db.merge(row)

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_price_index(db)
        seed_income_poverty(db)
        seed_hygiene_access(db)
        db.commit()
        print("Seeding completed.")
    finally:
        db.close()

if __name__ == "__main__":
    run()