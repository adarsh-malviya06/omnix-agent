# Standard Purchasing Procedures and Reorder Guidelines
Document ID: SOP-PROC-002
Category: Purchasing Procedures
Version: 1.3
Applies To: Central Procurement Desk, Inventory Controllers, Category Managers

## 1. Purchase Order Creation and Lifecycle Workflow
Every commercial procurement requirement must follow the structured six-step lifecycle:
1. **Deficit Identification**: Triggered automatically when available inventory falls below calculated reorder points or manually via stock audit.
2. **Vendor Sourcing & Comparison**: The procurement team must evaluate at least two active vendors for non-proprietary SKUs. Vendor ranking must balance price (40%), lead time (30%), and historical delivery reliability (30%).
3. **Reorder Quantity Calculation**: Reorder quantities must be calculated using:
   Suggested Quantity = max(Deficit, Safety Stock Buffer, Supplier Minimum Order Quantity).
   Orders must not round up arbitrarily unless required to fulfill master packaging cartons or supplier pallet restrictions.
4. **Draft PO Generation**: System creates purchase order in `draft` status detailing destination warehouse code, SKU lines, unit purchase rates in INR, and payment terms.
5. **Approval Submission**: PO transitions to `pending_approval` for review by designated financial authorities according to Policy POL-PROC-001.
6. **Transmission & Receipt**: Upon approval, PO is issued to the vendor. Partial shipments must be recorded under separate Goods Receipt Notes (GRN).

## 2. Emergency Out-of-Stock Replenishment Procedure
When a high-velocity product reaches `OUT_OF_STOCK` (0 available units):
- Expedited delivery terms may be authorized from secondary local suppliers even if quoted rates are up to 5% higher than primary contractual rates, provided the delivery lead time is 48 hours or less.
- Emergency orders require immediate verbal consent followed by digital sign-off from the Operations Manager within 12 hours of order placement.
