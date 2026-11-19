"""
API endpoints for Demand Forecasting and Stockout Risk.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from omnix.db.session import get_db
from omnix.ml.forecasting_service import forecast_product_demand
from omnix.schemas.forecasting import DemandForecastResponse

router = APIRouter(prefix="/forecasting", tags=["Demand Forecasting & Stockout Risk"])


@router.get("/{product_id}/{location_id}", response_model=DemandForecastResponse)
def get_product_forecast(
    product_id: int,
    location_id: int,
    horizon_days: int = Query(14, ge=1, le=90, description="Forward forecast window in calendar days"),
    db: Session = Depends(get_db),
):
    """
    Generate ML-driven forward demand forecasts and evaluated stockout risk metrics.
    """
    return forecast_product_demand(
        db, product_id=product_id, location_id=location_id, forecast_horizon_days=horizon_days
    )

