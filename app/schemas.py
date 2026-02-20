# app/schemas.py
# Pydantic v2-compatible schemas with OpenAPI examples.

from typing import Optional, List
from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# 1) Basket (CRUD)
# -------------------------------------------------------------------

class BasketItemBase(BaseModel):
    """Common fields for BasketItem create/update/read."""
    name: str = Field(..., min_length=1, max_length=255)
    unit_price: float = Field(..., ge=0)
    units_per_month: float = Field(..., ge=0)
    currency: str = Field("GBP", min_length=1, max_length=10)
    notes: Optional[str] = None

class BasketItemCreate(BasketItemBase):
    """POST body for creating a basket item."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "pads pack",
                "unit_price": 2.5,
                "units_per_month": 2,
                "currency": "GBP",
                "notes": "supermarket average"
            }
        }
    }

class BasketItemUpdate(BaseModel):
    """PUT body for updating a basket item (partial, all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit_price: Optional[float] = Field(None, ge=0)
    units_per_month: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=1, max_length=10)
    notes: Optional[str] = None
    model_config = {
        "json_schema_extra": {
            "example": {"unit_price": 3.0}
        }
    }

class BasketItemRead(BasketItemBase):
    """Response model for a basket item (includes id)."""
    id: int
    model_config = {
        "from_attributes": True,   # replaces orm_mode=True in Pydantic v2
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "pads pack",
                "unit_price": 2.5,
                "units_per_month": 2.0,
                "currency": "GBP",
                "notes": "supermarket average"
            }
        }
    }

# -------------------------------------------------------------------
# 2) Datasets (READ-ONLY)
# -------------------------------------------------------------------

class PriceIndexRead(BaseModel):
    """CPI personal care row (monthly)."""
    date: str
    cpi_index: float
    pct_change_mom: float | None = None
    pct_change_yoy: float | None = None
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "date": "2025-12-01",
                "cpi_index": 119.8,
                "pct_change_mom": 0.2,
                "pct_change_yoy": 3.4
            }
        }
    }

class IncomePovertyRead(BaseModel):
    """UK PIP percentile row (daily PPP in `avg_welfare`)."""
    year: int
    percentile: int
    avg_welfare: float
    welfare_type: str | None = None
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "year": 2018,
                "percentile": 20,
                "avg_welfare": 18.75,  # daily PPP
                "welfare_type": "income"
            }
        }
    }

class HygieneAccessRead(BaseModel):
    """UK hygiene proxy row (bathing facility %)."""
    country: str
    year: int
    indicator: str
    value: float
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "country": "United Kingdom",
                "year": 2018,
                "indicator": "bathing_facility",
                "value": 99.7
            }
        }
    }

# -------------------------------------------------------------------
# 3) Analytics
# -------------------------------------------------------------------

class InflationTrendPoint(BaseModel):
    date: str
    cpi_index: float
    pct_change_yoy: float | None = None

class InflationTrendResponse(BaseModel):
    from_: str | None = Field(None, alias="from")
    to: str | None = None
    points: List[InflationTrendPoint]
    model_config = {
        "json_schema_extra": {
            "example": {
                "from": "2018-01",
                "to": "2020-12",
                "points": [
                    {"date": "2018-01-01", "cpi_index": 100.5, "pct_change_yoy": 2.1},
                    {"date": "2018-02-01", "cpi_index": 100.6, "pct_change_yoy": 2.0}
                ]
            }
        }
    }

class BasketLine(BaseModel):
    name: str
    unit_price: float = Field(..., ge=0)
    units_per_month: float = Field(..., ge=0)
    currency: str = "GBP"
    notes: str | None = None

class CostEstimateRequest(BaseModel):
    """POST body for cost estimation. If `lines` is omitted/empty, API uses DB BasketItem rows."""
    lines: List[BasketLine] | None = None
    apply_yoy_cpi: bool = False
    model_config = {
        "json_schema_extra": {
            "example": {
                "apply_yoy_cpi": True,
                "lines": [
                    {"name": "pads pack", "unit_price": 2.5, "units_per_month": 2, "currency": "GBP"}
                ]
            }
        }
    }

class CostEstimateResponse(BaseModel):
    monthly_cost: float
    annual_cost: float
    used_lines: List[BasketLine]
    model_config = {
        "json_schema_extra": {
            "example": {
                "monthly_cost": 5.0,
                "annual_cost": 60.0,
                "used_lines": [
                    {"name": "pads pack", "unit_price": 2.5, "units_per_month": 2, "currency": "GBP"}
                ]
            }
        }
    }

class CostBurdenResponse(BaseModel):
    """Annual cost burden (ratio) compared against PIP annual PPP."""
    year: int
    percentile: int
    annual_cost: float
    avg_welfare_annual_ppp: float
    burden_ratio: float  # annual_cost / avg_welfare_annual_ppp
    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2018,
                "percentile": 20,
                "annual_cost": 60.0,
                "avg_welfare_annual_ppp": 7500.0,
                "burden_ratio": 0.008
            }
        }
    }

class SeverityScoreResponse(BaseModel):
    """Simple composite score combining affordability (burden) and hygiene severity."""
    year: int
    annual_cost: float
    avg_welfare_annual_ppp: float
    burden_ratio: float
    hygiene_value_pct: float
    hygiene_severity: float       # 1 - hygiene_value_pct/100
    combined_severity: float
    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2018,
                "annual_cost": 60.0,
                "avg_welfare_annual_ppp": 7500.0,
                "burden_ratio": 0.008,
                "hygiene_value_pct": 99.7,
                "hygiene_severity": 0.003,
                "combined_severity": 0.0037
            }
        }
    }