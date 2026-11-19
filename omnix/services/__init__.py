from omnix.services.alert_service import (
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    scan_and_generate_inventory_alerts,
)
from omnix.services.inventory_service import (
    get_all_products,
    get_inventory_positions,
    get_low_stock_items,
    get_movement_history,
    get_out_of_stock_items,
    get_product_by_id,
    get_product_by_sku,
    record_inventory_movement,
)
from omnix.services.procurement_service import (
    calculate_average_daily_demand,
    calculate_reorder_recommendation,
    create_procurement_recommendation,
    create_purchase_order_draft,
    get_dashboard_statistics,
    process_purchase_order_approval,
)
from omnix.services.settings_service import (
    get_all_settings,
    get_setting_value,
    set_setting_value,
)
from omnix.services.supplier_service import (
    calculate_supplier_score,
    compare_suppliers_for_product,
    get_all_suppliers,
    get_supplier_by_id,
    get_supplier_products,
)

__all__ = [
    "get_all_products",
    "get_product_by_id",
    "get_product_by_sku",
    "get_inventory_positions",
    "get_low_stock_items",
    "get_out_of_stock_items",
    "record_inventory_movement",
    "get_movement_history",
    "get_all_suppliers",
    "get_supplier_by_id",
    "get_supplier_products",
    "calculate_supplier_score",
    "compare_suppliers_for_product",
    "calculate_average_daily_demand",
    "calculate_reorder_recommendation",
    "create_procurement_recommendation",
    "create_purchase_order_draft",
    "process_purchase_order_approval",
    "get_dashboard_statistics",
    "get_setting_value",
    "set_setting_value",
    "get_all_settings",
    "scan_and_generate_inventory_alerts",
    "get_active_alerts",
    "get_all_alerts",
    "resolve_alert",
]
