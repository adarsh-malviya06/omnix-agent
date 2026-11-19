"""
Controlled, deterministic business tools callable by OMNIX LangGraph agents.
No raw SQL execution; strictly uses tested business service functions.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from omnix.core.exceptions import NotFoundException
from omnix.db.models import Product
from omnix.ml.forecasting_service import forecast_product_demand
from omnix.rag.retriever import retrieve_relevant_knowledge
from omnix.services.inventory_service import (
    get_all_products,
    get_inventory_positions,
    get_low_stock_items,
    get_movement_history,
    get_out_of_stock_items,
    get_product_by_id,
    get_product_by_sku,
)
from omnix.services.procurement_service import (
    calculate_reorder_recommendation,
    create_procurement_recommendation,
    create_purchase_order_draft,
    get_dashboard_statistics,
)
from omnix.services.supplier_service import (
    compare_suppliers_for_product,
    get_all_suppliers,
    get_supplier_by_id,
)


def tool_get_product_info(db: Session, sku_or_id: str) -> Dict[str, Any]:
    """Retrieve product metadata by SKU or ID."""
    if sku_or_id.isdigit():
        prod = get_product_by_id(db, int(sku_or_id))
    else:
        prod = get_product_by_sku(db, sku_or_id)
    return {
        "id": prod.id,
        "sku": prod.sku,
        "name": prod.name,
        "category": prod.category,
        "uom": prod.uom,
        "standard_cost": float(prod.standard_cost) if prod.standard_cost else 0.0,
        "reorder_point": prod.reorder_point,
        "safety_stock": prod.safety_stock,
        "organization_id": prod.organization_id,
    }


def tool_check_inventory_stock(
    db: Session,
    product_id: Optional[int] = None,
    location_id: Optional[int] = None,
    organization_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve stock levels, net available units, and health flags."""
    items = get_inventory_positions(
        db, organization_id=organization_id, location_id=location_id, product_id=product_id
    )
    return [
        {
            "product_id": itm.product_id,
            "product_name": itm.product.name,
            "product_sku": itm.product.sku,
            "location_id": itm.location_id,
            "location_name": itm.location.name,
            "quantity_on_hand": itm.quantity_on_hand,
            "quantity_reserved": itm.quantity_reserved,
            "quantity_available": itm.quantity_available,
            "is_low_stock": itm.is_low_stock,
            "is_out_of_stock": itm.is_out_of_stock,
            "unit_cost": float(itm.last_purchase_cost),
        }
        for itm in items
    ]


def tool_get_low_stock_alerts(db: Session, organization_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve all items currently below reorder thresholds."""
    items = get_low_stock_items(db, organization_id=organization_id)
    out_items = get_out_of_stock_items(db, organization_id=organization_id)
    all_alerts = items + out_items
    return [
        {
            "product_id": itm.product_id,
            "product_name": itm.product.name,
            "product_sku": itm.product.sku,
            "location_id": itm.location_id,
            "quantity_on_hand": itm.quantity_on_hand,
            "safety_min": itm.product.reorder_point,
            "status": "OUT_OF_STOCK" if itm.is_out_of_stock else "LOW_STOCK",
        }
        for itm in all_alerts
    ]


def tool_get_ml_forecast(
    db: Session, product_id: int, location_id: int, horizon_days: int = 14
) -> Dict[str, Any]:
    """Execute Scikit-Learn demand forecast and stockout risk assessment."""
    forecast = forecast_product_demand(
        db, product_id=product_id, location_id=location_id, forecast_horizon_days=horizon_days
    )
    return {
        "product_id": forecast.product_id,
        "product_name": forecast.product_name,
        "total_forecasted_demand": forecast.total_forecasted_demand,
        "average_daily_demand": forecast.average_daily_forecast,
        "stockout_risk_level": forecast.stockout_risk.risk_level,
        "days_until_stockout": forecast.stockout_risk.days_until_stockout,
        "estimated_stockout_date": str(forecast.stockout_risk.estimated_stockout_date) if forecast.stockout_risk.estimated_stockout_date else None,
        "lead_time_days": forecast.stockout_risk.lead_time_days,
        "lead_time_demand": forecast.stockout_risk.lead_time_demand,
        "model_used": forecast.evaluation.model_name,
        "model_mae": forecast.evaluation.mae,
        "model_rmse": forecast.evaluation.rmse,
    }


def tool_compare_suppliers(db: Session, product_id: int) -> Dict[str, Any]:
    """Execute multi-attribute vendor comparison."""
    comp = compare_suppliers_for_product(db, product_id=product_id)
    return {
        "product_id": comp.product_id,
        "product_name": comp.product_name,
        "quotes": [
            {
                "supplier_id": q.supplier_id,
                "supplier_name": q.supplier_name,
                "supplier_code": q.supplier_code,
                "unit_price": float(q.unit_price),
                "lead_days": q.lead_days,
                "moq": q.moq,
                "reliability_score": float(q.reliability_score),
                "composite_score": q.composite_score,
                "is_recommended": q.is_recommended,
            }
            for q in comp.quotes
        ],
    }


def tool_search_procurement_policies(query: str, top_k: int = 2) -> Dict[str, Any]:
    """Retrieve relevant procurement policies using ChromaDB RAG."""
    rag_res = retrieve_relevant_knowledge(query=query, top_k=top_k)
    return {
        "has_content": rag_res.has_relevant_content,
        "sources": [
            {
                "document_id": c.document_id,
                "title": c.title,
                "category": c.category,
                "content": c.content,
                "similarity": c.similarity_score,
            }
            for c in rag_res.chunks
        ],
    }


def tool_calculate_reorder_order(
    db: Session, product_id: int, location_id: int
) -> Dict[str, Any]:
    """Execute deterministic inventory equation and safety reorder formula."""
    calc = calculate_reorder_recommendation(db, product_id=product_id, location_id=location_id)
    return {
        "product_id": calc.product_id,
        "location_id": calc.location_id,
        "current_stock": calc.current_stock,
        "available_stock": calc.available_stock,
        "calculated_reorder_point": calc.calculated_reorder_point,
        "is_reorder_needed": calc.is_reorder_needed,
        "suggested_order_quantity": calc.suggested_order_quantity,
        "best_supplier_id": calc.best_supplier_id,
        "best_supplier_name": calc.best_supplier_name,
        "estimated_unit_cost": float(calc.estimated_unit_cost),
        "estimated_total_cost": float(calc.estimated_total_cost),
        "data_source": calc.data_source,
    }


def tool_generate_purchase_recommendation(
    db: Session, product_id: int, location_id: int
) -> Dict[str, Any]:
    """Create a persistent pending recommendation entry."""
    rec = create_procurement_recommendation(db, product_id=product_id, location_id=location_id)
    return {
        "recommendation_id": rec.id,
        "product_id": rec.product_id,
        "product_name": rec.product.name,
        "suggested_supplier_id": rec.suggested_supplier_id,
        "suggested_quantity": rec.suggested_quantity,
        "estimated_cost": float(rec.estimated_cost),
        "status": rec.status.value,
        "reasoning": rec.reasoning,
    }
