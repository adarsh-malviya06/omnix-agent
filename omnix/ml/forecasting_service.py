"""
Machine Learning & Statistical Demand Forecasting Service.

Capabilities:
1. Time-series data preparation and quality audit (missing dates, zero demand).
2. Simple baseline forecasting: Rolling Moving Average & Historical Mean.
3. Machine Learning forecasting: Ridge Linear Regression with lag features & calendar signals (Day of Week).
4. Time-based holdout evaluation: Computes out-of-sample MAE and RMSE against the baseline.
5. Stockout risk synthesis: Combines current stock, lead time, incoming orders, and daily demand forecasts.
"""

from datetime import date, datetime, timedelta
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy.orm import Session

from omnix.core.exceptions import NotFoundException
from omnix.db.base import PurchaseOrderStatus
from omnix.db.models import (
    DemandHistory,
    Inventory,
    Location,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierProduct,
)
from omnix.schemas.forecasting import (
    DailyForecastItem,
    DemandForecastResponse,
    ModelEvaluationMetrics,
    StockoutRiskAssessment,
)


def load_demand_series(
    db: Session, product_id: int, location_id: int
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Extract, sort, and complete historical daily demand records into a continuous daily time series.
    Returns (DataFrame, data_quality_notes).
    """
    records = (
        db.query(DemandHistory)
        .filter(
            DemandHistory.product_id == product_id,
            DemandHistory.location_id == location_id,
        )
        .order_by(DemandHistory.record_date.asc())
        .all()
    )

    if not records:
        return pd.DataFrame(), "No historical demand data available for this product and location."

    data = [
        {"date": r.record_date, "demand": float(r.net_demand)}
        for r in records
    ]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates(subset=["date"])

    # Re-index to continuous daily frequency to detect/fill any gaps
    full_idx = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_idx)
    df.index.name = "date"

    missing_count = int(df["demand"].isna().sum())
    # Forward-fill or zero-fill missing dates
    df["demand"] = df["demand"].fillna(0.0)
    df = df.reset_index()

    notes = []
    if missing_count > 0:
        notes.append(f"{missing_count} missing date(s) detected and zero-filled.")
    if len(df) < 14:
        notes.append(f"Limited history ({len(df)} days). Model relies on baseline statistical estimates.")

    quality_notes = " ".join(notes) if notes else "Full continuous historical series available."
    return df, quality_notes


def evaluate_and_train_models(
    df: pd.DataFrame, test_days: int = 7
) -> Tuple[ModelEvaluationMetrics, callable]:
    """
    Perform a time-based train/test split.
    Fits both a baseline Moving Average and a Ridge Regression model.
    Computes out-of-sample MAE & RMSE, selecting the model that yields lowest RMSE.
    Returns (metrics, forecast_predictor_func).
    """
    n = len(df)
    # When sample data is small (< 14 days), we cannot do a 7-day holdout safely
    if n < 14:
        # Fallback to pure rolling mean
        mean_val = float(df["demand"].mean()) if n > 0 else 5.0
        metrics = ModelEvaluationMetrics(
            mae=0.0,
            rmse=0.0,
            baseline_mae=0.0,
            baseline_rmse=0.0,
            r2_score=None,
            test_days=0,
            model_name="Historical Mean (Small Sample Fallback)",
        )
        def fallback_predict(horizon_days: int, start_date: date) -> List[float]:
            return [round(max(0.0, mean_val), 2) for _ in range(horizon_days)]
        return metrics, fallback_predict

    # Time-based split: Hold out the most recent `test_days`
    train_df = df.iloc[:-test_days].copy()
    test_df = df.iloc[-test_days:].copy()

    # 1. Baseline: 7-day Moving Average of the training set
    baseline_pred_val = float(train_df["demand"].tail(7).mean())
    baseline_preds = np.full(len(test_df), baseline_pred_val)

    b_mae = float(mean_absolute_error(test_df["demand"], baseline_preds))
    b_rmse = float(np.sqrt(mean_squared_error(test_df["demand"], baseline_preds)))

    # 2. Machine Learning: Feature Engineered Ridge Regression
    # Features: Day of week, 3-day lag, 7-day lag
    def build_features(data_series: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        feats, targets = [], []
        demands = data_series["demand"].values
        dates = data_series["date"]
        for i in range(7, len(demands)):
            dow = int(dates.iloc[i].day_of_week)
            lag1 = demands[i - 1]
            lag3 = demands[i - 3]
            lag7 = demands[i - 7]
            roll_mean7 = float(np.mean(demands[i - 7:i]))
            feats.append([dow, lag1, lag3, lag7, roll_mean7])
            targets.append(demands[i])
        return np.array(feats), np.array(targets)

    X_train, y_train = build_features(train_df)

    # If training points are sufficient for regression
    ml_mae, ml_rmse = b_mae, b_rmse
    use_ml = False
    model = Ridge(alpha=1.0)

    if len(X_train) >= 10:
        model.fit(X_train, y_train)
        # Evaluate on test set sequentially
        full_df = pd.concat([train_df, test_df]).reset_index(drop=True)
        test_preds = []
        for i in range(len(train_df), len(full_df)):
            dow = int(full_df["date"].iloc[i].day_of_week)
            lag1 = full_df["demand"].iloc[i - 1]
            lag3 = full_df["demand"].iloc[i - 3]
            lag7 = full_df["demand"].iloc[i - 7]
            roll_mean7 = float(np.mean(full_df["demand"].iloc[i - 7:i]))
            pred = float(model.predict([[dow, lag1, lag3, lag7, roll_mean7]])[0])
            test_preds.append(max(0.0, pred))

        ml_mae = float(mean_absolute_error(test_df["demand"], test_preds))
        ml_rmse = float(np.sqrt(mean_squared_error(test_df["demand"], test_preds)))

        # Compare model against baseline: Only promote ML model if it performs competitively
        if ml_rmse <= b_rmse * 1.05:  # within 5% or superior
            use_ml = True

    # Retrain selected model on 100% of available data for forward forecasting
    if use_ml:
        X_all, y_all = build_features(df)
        model.fit(X_all, y_all)
        selected_model_name = "Ridge Regression (Lag & Day-of-Week Features)"
        final_mae = round(ml_mae, 2)
        final_rmse = round(ml_rmse, 2)

        def predict_future(horizon_days: int, start_date: date) -> List[float]:
            history = list(df["demand"].values)
            future_preds = []
            cur_date = pd.to_datetime(start_date)
            for _ in range(horizon_days):
                dow = int(cur_date.day_of_week)
                lag1 = history[-1]
                lag3 = history[-3]
                lag7 = history[-7]
                roll_mean7 = float(np.mean(history[-7:]))
                pred = float(model.predict([[dow, lag1, lag3, lag7, roll_mean7]])[0])
                pred = max(0.0, round(pred, 2))
                future_preds.append(pred)
                history.append(pred)
                cur_date += timedelta(days=1)
            return future_preds
    else:
        selected_model_name = "Simple Moving Average (7-Day Rolling Baseline)"
        final_mae = round(b_mae, 2)
        final_rmse = round(b_rmse, 2)
        rolling_val = float(df["demand"].tail(7).mean())

        def predict_future(horizon_days: int, start_date: date) -> List[float]:
            return [round(max(0.0, rolling_val), 2) for _ in range(horizon_days)]

    metrics = ModelEvaluationMetrics(
        mae=final_mae,
        rmse=final_rmse,
        baseline_mae=round(b_mae, 2),
        baseline_rmse=round(b_rmse, 2),
        r2_score=None,
        test_days=test_days,
        model_name=selected_model_name,
    )
    return metrics, predict_future


def calculate_stockout_risk(
    db: Session,
    product_id: int,
    location_id: int,
    daily_forecasts: List[DailyForecastItem],
    safety_stock: int,
) -> StockoutRiskAssessment:
    """
    Synthesize on-hand stock, approved purchase orders in transit, supplier lead time,
    and daily forecasted demand to evaluate stockout date and risk severity.
    """
    # 1. Fetch current inventory position
    inv = (
        db.query(Inventory)
        .filter_by(product_id=product_id, location_id=location_id)
        .first()
    )
    current_stock = inv.quantity_on_hand if inv else 0
    reserved_stock = inv.quantity_reserved if inv else 0
    available_stock = max(0, current_stock - reserved_stock)

    # 2. Fetch incoming stock from approved / ordered POs
    incoming_query = (
        db.query(PurchaseOrderItem.quantity)
        .join(PurchaseOrder)
        .filter(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrder.destination_location_id == location_id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.ORDERED]),
        )
        .all()
    )
    incoming_stock = sum(item[0] for item in incoming_query)

    # 3. Determine best supplier lead time
    sp = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.product_id == product_id,
            SupplierProduct.is_available == True,
        )
        .order_by(SupplierProduct.lead_days.asc())
        .first()
    )
    lead_time_days = sp.lead_days if sp else 7

    # 4. Compute depletion trajectory over daily forecasts
    cumulative_demand = 0.0
    stockout_day_index = None
    simulated_stock = float(available_stock)

    for idx, f_item in enumerate(daily_forecasts):
        simulated_stock -= f_item.predicted_demand
        if simulated_stock <= 0 and stockout_day_index is None:
            # Fraction of day remaining before zero
            prior_stock = simulated_stock + f_item.predicted_demand
            burn_rate = f_item.predicted_demand if f_item.predicted_demand > 0 else 1.0
            fraction = prior_stock / burn_rate
            stockout_day_index = idx + fraction

    # Lead time demand
    daily_rates = [f.predicted_demand for f in daily_forecasts]
    avg_burn = float(np.mean(daily_rates)) if daily_rates else 5.0
    lead_time_demand = round(avg_burn * lead_time_days, 2)

    # Available stock at replenishment horizon
    # Deficit at lead time = (Available + Incoming) - (Lead Time Demand + Safety Stock)
    net_effective_stock = available_stock + incoming_stock
    deficit_at_lead = round(float((lead_time_demand + safety_stock) - net_effective_stock), 2)

    # Determine risk category
    if available_stock <= 0:
        risk_level = "CRITICAL"
    elif stockout_day_index is not None and stockout_day_index <= lead_time_days:
        risk_level = "CRITICAL"
    elif deficit_at_lead > 0:
        risk_level = "HIGH"
    elif net_effective_stock <= (lead_time_demand + safety_stock * 1.5):
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    days_until_stockout = round(stockout_day_index, 1) if stockout_day_index is not None else None
    est_date = None
    if days_until_stockout is not None:
        est_date = date.today() + timedelta(days=math.floor(days_until_stockout))

    return StockoutRiskAssessment(
        risk_level=risk_level,
        days_until_stockout=days_until_stockout,
        estimated_stockout_date=est_date,
        current_stock=current_stock,
        reserved_stock=reserved_stock,
        available_stock=available_stock,
        safety_stock=safety_stock,
        incoming_stock=incoming_stock,
        lead_time_days=lead_time_days,
        lead_time_demand=lead_time_demand,
        deficit_at_lead_time=max(0.0, deficit_at_lead),
    )


def forecast_product_demand(
    db: Session,
    product_id: int,
    location_id: int,
    forecast_horizon_days: int = 14,
) -> DemandForecastResponse:
    """
    Main operational entry point for demand forecasting and stockout risk assessment.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException(f"Product ID {product_id} not found.")

    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise NotFoundException(f"Location ID {location_id} not found.")

    # 1. Load series
    df, quality_notes = load_demand_series(db, product_id, location_id)

    # 2. Train and evaluate
    metrics, predictor = evaluate_and_train_models(df, test_days=7)

    # 3. Generate future daily forecast items
    start_date = date.today() + timedelta(days=1)
    raw_predictions = predictor(forecast_horizon_days, start_date)

    daily_items = []
    cur_d = start_date
    std_err = metrics.rmse if metrics.rmse > 0 else 1.5

    for pred in raw_predictions:
        daily_items.append(
            DailyForecastItem(
                date=cur_d,
                predicted_demand=round(pred, 2),
                lower_bound=round(max(0.0, pred - 1.96 * std_err), 2),
                upper_bound=round(pred + 1.96 * std_err, 2),
            )
        )
        cur_d += timedelta(days=1)

    # 4. Stockout risk assessment
    safety_stock = product.safety_stock or 0
    risk = calculate_stockout_risk(db, product_id, location_id, daily_items, safety_stock)

    total_demand = round(sum(d.predicted_demand for d in daily_items), 2)
    avg_daily = round(total_demand / forecast_horizon_days, 2) if forecast_horizon_days > 0 else 0.0

    return DemandForecastResponse(
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        location_id=location_id,
        forecast_horizon_days=forecast_horizon_days,
        historical_days_available=len(df),
        total_forecasted_demand=total_demand,
        average_daily_forecast=avg_daily,
        daily_forecasts=daily_items,
        stockout_risk=risk,
        evaluation=metrics,
        data_quality_notes=quality_notes,
    )
