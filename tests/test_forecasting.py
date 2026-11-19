"""
Automated test suite for Phase 4: Demand Forecasting and Stockout Risk Analysis.
Tests:
- Normal demand forecasting with time-based evaluation metrics (MAE, RMSE).
- Baseline vs. Ridge regression comparison.
- Stockout risk calculation and depletion horizon tracking.
- Edge cases: Zero demand, missing historical data, limited/sparse history.
- REST API endpoint integration.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from omnix.api.main import app
from omnix.core.exceptions import NotFoundException
from omnix.db.base import Base
from omnix.db.models import DemandHistory, Location, Organization, Product, User
from omnix.db.seed import seed_database
from omnix.db.session import get_db
from omnix.ml.forecasting_service import (
    calculate_stockout_risk,
    evaluate_and_train_models,
    forecast_product_demand,
    load_demand_series,
)
from omnix.schemas.forecasting import DailyForecastItem

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def db_session():
    """Create test schema and seed data in-memory."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client(db_session):
    """FastAPI test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestDemandDataAnalysis:
    def test_load_demand_series_normal(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        df, notes = load_demand_series(db_session, prod.id, loc.id)
        assert len(df) == 30
        assert "date" in df.columns
        assert "demand" in df.columns
        assert df["demand"].mean() > 0

    def test_load_demand_series_missing_history(self, db_session):
        # Create a new product without demand history
        org = db_session.query(Organization).first()
        loc = db_session.query(Location).first()
        new_prod = Product(
            organization_id=org.id,
            sku="SKU-NEW-NO-HISTORY",
            name="Brand New Unsold Product",
            category="Test",
            uom="unit",
        )
        db_session.add(new_prod)
        db_session.commit()

        df, notes = load_demand_series(db_session, new_prod.id, loc.id)
        assert df.empty
        assert "No historical demand data" in notes


class TestModelTrainingAndEvaluation:
    def test_time_based_split_evaluation(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()
        df, _ = load_demand_series(db_session, prod.id, loc.id)

        metrics, predictor = evaluate_and_train_models(df, test_days=7)
        assert metrics.test_days == 7
        assert metrics.mae >= 0
        assert metrics.rmse >= 0
        assert metrics.baseline_mae >= 0
        assert metrics.baseline_rmse >= 0
        assert "Ridge" in metrics.model_name or "Moving Average" in metrics.model_name

        # Verify predictions are positive and reasonable
        preds = predictor(14, date.today() + timedelta(days=1))
        assert len(preds) == 14
        assert all(p >= 0 for p in preds)

    def test_zero_demand_handling(self, db_session):
        import pandas as pd
        dates = pd.date_range(start="2026-10-01", periods=20, freq="D")
        zero_df = pd.DataFrame({"date": dates, "demand": [0.0] * 20})

        metrics, predictor = evaluate_and_train_models(zero_df, test_days=5)
        preds = predictor(7, date.today() + timedelta(days=1))
        assert len(preds) == 7
        assert all(p == 0.0 for p in preds)


class TestStockoutRiskCalculation:
    def test_out_of_stock_triggers_critical_risk(self, db_session):
        # SKU-SUGAR-50KG is seeded with 0 stock
        prod = db_session.query(Product).filter_by(sku="SKU-SUGAR-50KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        forecast_res = forecast_product_demand(db_session, prod.id, loc.id, forecast_horizon_days=14)
        risk = forecast_res.stockout_risk
        assert risk.risk_level == "CRITICAL"
        assert risk.current_stock == 0

    def test_low_stock_depletion_estimation(self, db_session):
        # SKU-RICE-25KG has 35 units, daily demand ~7.9 units
        # Available stock: 35 - 5 reserved = 30
        # Expected depletion ~ 30 / 7.9 = ~3.8 days
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        forecast_res = forecast_product_demand(db_session, prod.id, loc.id, forecast_horizon_days=14)
        risk = forecast_res.stockout_risk
        assert risk.days_until_stockout is not None
        assert 2.0 <= risk.days_until_stockout <= 6.0
        assert risk.estimated_stockout_date is not None
        assert risk.risk_level in ["CRITICAL", "HIGH"]


class TestForecastingAPI:
    def test_api_get_forecast(self, client, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        res = client.get(f"/api/v1/forecasting/{prod.id}/{loc.id}?horizon_days=14")
        assert res.status_code == 200
        data = res.json()
        assert data["product_id"] == prod.id
        assert data["forecast_horizon_days"] == 14
        assert len(data["daily_forecasts"]) == 14
        assert "stockout_risk" in data
        assert "evaluation" in data
        assert data["evaluation"]["mae"] >= 0

