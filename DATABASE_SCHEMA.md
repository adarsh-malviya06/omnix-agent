# OMNIX Agent — Database Schema Documentation

This document describes the relational database schema implemented in SQLAlchemy for the OMNIX Agent system. The default database engine is SQLite (`sqlite:///./omnix.db`) with full support for PostgreSQL.

---

## Entity Relationship Overview

```
[Organization]
       ├── [User]
       ├── [Location]
       │       └── [Inventory] ◄── [Product] ◄── [DemandHistory]
       │               │              ▲
       │               ▼              │
       │       [InventoryMovement]    │
       │                              │
       ├── [Supplier] ────────► [SupplierProduct]
       │       │
       │       ▼
       ├── [PurchaseOrder] ──► [PurchaseOrderItem]
       │       │
       │       ▼
       ├── [Approval]
       │
       ├── [Recommendation]
       │
       ├── [InventoryAlert]
       │
       └── [AuditLog]

[SystemSetting] (Key-Value Configuration)
```

---

## Tables and Columns

### 1. `organizations`
Primary multi-tenant boundary for wholesale, distribution, and retail entities.
- `id` (INTEGER, PK, Auto-increment)
- `name` (VARCHAR(150), Unique, Not Null)
- `business_type` (VARCHAR(50), Enum: `wholesale`, `distribution`, `retail`, `supermarket`)
- `gst_number` (VARCHAR(15), Nullable)
- `currency` (VARCHAR(3), Default: `'INR'`)
- `created_at`, `updated_at` (TIMESTAMP)

### 2. `users`
System actors and staff eligible for procurement review and authorization.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `email` (VARCHAR(150), Unique, Not Null)
- `full_name` (VARCHAR(100), Not Null)
- `role` (VARCHAR(50), Enum: `admin`, `manager`, `staff`, `viewer`)
- `is_active` (BOOLEAN, Default: `True`)
- `created_at`, `updated_at` (TIMESTAMP)

### 3. `locations`
Physical warehouse, distribution center, or retail store facilities.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `code` (VARCHAR(50), Unique, Not Null)
- `name` (VARCHAR(150), Not Null)
- `location_type` (VARCHAR(50), Enum: `warehouse`, `store`, `distribution_center`)
- `city` (VARCHAR(100))
- `state` (VARCHAR(100))
- `pincode` (VARCHAR(20))
- `is_active` (BOOLEAN, Default: `True`)

### 4. `products`
Master catalog items and SKUs with safety stock thresholds.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `sku` (VARCHAR(50), Unique, Not Null)
- `name` (VARCHAR(200), Not Null)
- `category` (VARCHAR(100), Not Null)
- `uom` (VARCHAR(20), e.g., 'BAG_25KG', 'TIN_15L')
- `standard_cost` (NUMERIC(14,2), in INR)
- `reorder_point` (INTEGER, Safety minimum threshold)
- `reorder_quantity` (INTEGER, Economic batch size)
- `safety_stock` (INTEGER, Default: `0`)
- `is_active` (BOOLEAN, Default: `True`)

### 5. `inventory`
Live stock position for a product at a physical location.
- `id` (INTEGER, PK)
- `product_id` (INTEGER, FK -> `products.id`)
- `location_id` (INTEGER, FK -> `locations.id`)
- `quantity_on_hand` (INTEGER, >= 0, physically present)
- `quantity_reserved` (INTEGER, >= 0, committed to outgoing orders)
- `last_purchase_cost` (NUMERIC(14,2), Unit cost in INR)
- `UniqueConstraint("product_id", "location_id")`
- *Computed properties*:
  - `quantity_available` = `max(0, quantity_on_hand - quantity_reserved)`
  - `is_low_stock` = `quantity_on_hand <= product.reorder_point`
  - `is_out_of_stock` = `quantity_on_hand == 0`

### 6. `inventory_movements`
Immutable ledger of all stock transactions.
- `id` (INTEGER, PK)
- `product_id` (INTEGER, FK -> `products.id`)
- `location_id` (INTEGER, FK -> `locations.id`)
- `movement_type` (VARCHAR(50), Enum: `purchase_receipt`, `sale`, `transfer_in`, `transfer_out`, `adjustment_positive`, `adjustment_negative`, `return`, `damage`)
- `quantity_delta` (INTEGER, non-zero adjustment)
- `quantity_after` (INTEGER, resulting on-hand stock)
- `unit_cost` (NUMERIC(14,2), optional)
- `total_cost` (NUMERIC(14,2), optional)
- `reference_number` (VARCHAR(100), e.g., PO number or Invoice ID)
- `performed_at` (TIMESTAMP)

### 7. `suppliers`
Vendor network profiles and performance tracking.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `code` (VARCHAR(50), Unique, Not Null)
- `name` (VARCHAR(150), Not Null)
- `contact_person` (VARCHAR(100))
- `contact_email` (VARCHAR(150))
- `contact_phone` (VARCHAR(30))
- `reliability_score` (NUMERIC(5,2), 0-100 historical rating)
- `avg_lead_days` (INTEGER, average fulfillment lead time)
- `payment_terms` (VARCHAR(100), e.g., 'Net 30')
- `is_active` (BOOLEAN, Default: `True`)

### 8. `supplier_products`
Vendor contract quotes, catalog prices, and MOQs.
- `id` (INTEGER, PK)
- `supplier_id` (INTEGER, FK -> `suppliers.id`)
- `product_id` (INTEGER, FK -> `products.id`)
- `supplier_sku` (VARCHAR(100))
- `unit_price` (NUMERIC(14,2), in INR)
- `lead_days` (INTEGER, vendor quote delivery window)
- `moq` (INTEGER, Minimum Order Quantity)
- `is_preferred` (BOOLEAN, Default: `False`)

### 9. `demand_history`
Daily consumption and sales data driving Scikit-Learn ML forecasts.
- `id` (INTEGER, PK)
- `product_id` (INTEGER, FK -> `products.id`)
- `location_id` (INTEGER, FK -> `locations.id`)
- `record_date` (DATE, Not Null)
- `quantity_sold` (INTEGER, >= 0)
- `quantity_returned` (INTEGER, >= 0)
- `revenue` (NUMERIC(14,2), in INR)
- *Computed property*: `net_demand` = `max(0, quantity_sold - quantity_returned)`

### 10. `purchase_orders`
Purchase order records governed by human-in-the-loop authorization.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `po_number` (VARCHAR(50), Unique, e.g., 'PO-2026-0001')
- `supplier_id` (INTEGER, FK -> `suppliers.id`)
- `destination_location_id` (INTEGER, FK -> `locations.id`)
- `status` (VARCHAR(50), Enum: `draft`, `pending_approval`, `approved`, `rejected`, `ordered`, `partially_received`, `received`, `cancelled`)
- `currency` (VARCHAR(3), Default: `'INR'`)
- `total_amount` (NUMERIC(14,2), in INR)
- `notes` (TEXT)
- `order_date` (TIMESTAMP)

### 11. `purchase_order_items`
Individual line items on purchase orders.
- `id` (INTEGER, PK)
- `purchase_order_id` (INTEGER, FK -> `purchase_orders.id`)
- `product_id` (INTEGER, FK -> `products.id`)
- `quantity` (INTEGER, > 0)
- `unit_price` (NUMERIC(14,2))
- `subtotal` (NUMERIC(14,2))

### 12. `recommendations`
AI/rule-generated replenishment suggestions awaiting human approval.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`)
- `product_id` (INTEGER, FK -> `products.id`)
- `location_id` (INTEGER, FK -> `locations.id`)
- `suggested_supplier_id` (INTEGER, FK -> `suppliers.id`, Nullable)
- `suggested_quantity` (INTEGER)
- `current_stock` (INTEGER)
- `reorder_point` (INTEGER)
- `estimated_cost` (NUMERIC(14,2), in INR)
- `status` (VARCHAR(50), Enum: `pending`, `accepted`, `rejected`, `expired`)
- `reasoning` (TEXT)
- `purchase_order_id` (INTEGER, FK -> `purchase_orders.id`, Nullable)

### 13. `approvals`
Audit records of human sign-off or rejection on purchase orders.
- `id` (INTEGER, PK)
- `purchase_order_id` (INTEGER, FK -> `purchase_orders.id`)
- `user_id` (INTEGER, FK -> `users.id`)
- `action` (VARCHAR(50), Enum: `approved`, `rejected`, `escalated`)
- `comments` (TEXT)
- `decided_at` (TIMESTAMP)

### 14. `audit_logs`
Immutable compliance and security trail for all critical operations.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`, Nullable)
- `user_id` (INTEGER, FK -> `users.id`, Nullable)
- `event_type` (VARCHAR(50), Enum: `po_created`, `po_approved`, `po_rejected`, `stock_adjusted`, `threshold_updated`, `system_event`)
- `actor` (VARCHAR(100), User name or Agent service name)
- `action` (VARCHAR(200))
- `details` (TEXT)
- `created_at` (TIMESTAMP)

### 15. `system_settings`
Persistent key-value configuration surviving restarts.
- `id` (INTEGER, PK)
- `key` (VARCHAR(100), Unique, e.g., `'max_auto_approval_limit'`)
- `value` (TEXT, e.g., `'75000.00'`)
- `category` (VARCHAR(50), e.g., `'governance'`, `'inventory'`)
- `description` (VARCHAR(255))
- `created_at`, `updated_at` (TIMESTAMP)

### 16. `inventory_alerts`
Persistent monitoring warnings for stockouts, deficits, and risks.
- `id` (INTEGER, PK)
- `organization_id` (INTEGER, FK -> `organizations.id`, Nullable)
- `product_id` (INTEGER, FK -> `products.id`)
- `location_id` (INTEGER, FK -> `locations.id`)
- `alert_type` (VARCHAR(50), e.g., `LOW_STOCK`, `OUT_OF_STOCK`, `HIGH_STOCKOUT_RISK`)
- `severity` (VARCHAR(20), Enum: `INFO`, `WARNING`, `CRITICAL`)
- `title` (VARCHAR(200))
- `message` (TEXT)
- `current_stock` (INTEGER)
- `threshold_value` (INTEGER)
- `is_resolved` (BOOLEAN, Default: `False`)
- `resolved_at` (TIMESTAMP, Nullable)
- `resolved_by` (VARCHAR(100), Nullable)
- `resolution_notes` (VARCHAR(255), Nullable)
