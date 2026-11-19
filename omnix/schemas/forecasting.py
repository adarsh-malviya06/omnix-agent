"""
Pydantic schemas for Machine Learning Demand Forecasting and Stockout Risk.
"""

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DailyForecastItem(BaseModel):
    """Forecasted demand for an individual calendar day."""
    date: date
    predicted_demand: float = Field(description="Point estimate of unit demand")
    lower_bound: float = Field(description="Lower confidence interval estimate (non-negative)")
    upper_bound: float = Field(description="Upper confidence interval estimate")


class ModelEvaluationMetrics(BaseModel):
    """Model evaluation metrics from time-series cross-validation / holdout split."""
    mae: float = Field(description="Mean Absolute Error on holdout test set")
    rmse: float = Field(description="Root Mean Squared Error on holdout test set")
    baseline_mae: float = Field(description="Simple Moving Average baseline MAE")
    baseline_rmse: float = Field(description="Simple Moving Average baseline RMSE")
    r2_score: Optional[float] = Field(None, description="Coefficient of determination, if applicable")
    test_days: int = Field(description="Number of evaluation days in holdout test set")
    model_name: str = Field(description="Winning model applied for forecasting")


class StockoutRiskAssessment(BaseModel):
    """Comprehensive stockout risk assessment combining stock, lead time, and forecast."""
    risk_level: str = Field(description="'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'")
    days_until_stockout: Optional[float] = Field(
        None, description="Estimated number of operational days before on-hand units deplete"
    )
    estimated_stockout_date: Optional[date] = Field(
        None, description="Calendar date of expected stock exhaustion, if within horizon"
    )
    current_stock: int
    reserved_stock: int
    available_stock: int
    safety_stock: int
    incoming_stock: int = Field(default=0, description="Approved PO units in transit")
    lead_time_days: int
    lead_time_demand: float = Field(description="Expected total demand over supplier lead time")
    deficit_at_lead_time: float = Field(description="Deficit below safety stock at replenishment horizon")


class DemandForecastResponse(BaseModel):
    """Structured response contract for product demand forecasting and stockout risk."""
    product_id: int
    product_name: str
    product_sku: str
    location_id: int
    forecast_horizon_days: int
    historical_days_available: int
    total_forecasted_demand: float
    average_daily_forecast: float
    daily_forecasts: List[DailyForecastItem]
    stockout_risk: StockoutRiskAssessment
    evaluation: ModelEvaluationMetrics
    data_quality_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

