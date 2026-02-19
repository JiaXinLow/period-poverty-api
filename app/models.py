from sqlalchemy import Column, Integer, Float, String, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class PriceIndex(Base):
    __tablename__ = "price_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[Date] = mapped_column(Date, index=True, unique=True, nullable=False)
    cpi_index: Mapped[float] = mapped_column(Float, nullable=False)
    pct_change_mom: Mapped[float | None] = mapped_column(Float)
    pct_change_yoy: Mapped[float | None] = mapped_column(Float)

class IncomePoverty(Base):
    __tablename__ = "income_poverty"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    percentile: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 1..100
    avg_welfare: Mapped[float] = mapped_column(Float, nullable=False)            # daily PPP in your processed CSV (annual also available if you choose)
    welfare_type: Mapped[str | None] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint("year", "percentile", name="uq_income_poverty_year_percentile"),
    )

class HygieneAccess(Base):
    __tablename__ = "hygiene_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String, index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    indicator: Mapped[str] = mapped_column(String, index=True, nullable=False)   # e.g., 'bathing_facility'
    value: Mapped[float] = mapped_column(Float, nullable=False)                  # percentage 0..100

    __table_args__ = (
        UniqueConstraint("country", "year", "indicator", name="uq_hygiene_country_year_indicator"),
    )

# CRUD-focused model for the "basket" concept, which combines price and access data into a single cost estimate for a set of essential items.
class BasketItem(Base):
    __tablename__ = "basket_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # you can remove unique=True if you want duplicates
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)        # e.g., 2.50 (GBP)
    units_per_month: Mapped[float] = mapped_column(Float, nullable=False)   # e.g., 2 packs/month
    currency: Mapped[str] = mapped_column(String, nullable=False, default="GBP")
    notes: Mapped[str | None] = mapped_column(String)                       # optional