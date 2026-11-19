# Warehouse Inbound Receiving and Inventory Quality Control Operating Procedures
Document ID: SOP-WH-004
Category: Operating Procedures
Version: 2.0
Location: All Distribution Centers and Warehouse Hubs

## 1. Inbound Shipment Arrival and Unloading
1. **Gate Verification**: Before allowing delivery trucks into loading bays, the security supervisor must match the vendor delivery challan against an active, approved OMNIX Purchase Order (status `approved` or `ordered`). Unapproved deliveries must be turned away.
2. **Physical Count & Batch Inspection**: Receiving staff must count all physical units (bags, cartons, tins). Damaged containers must be isolated immediately in the quarantine staging area.
3. **Goods Receipt Note (GRN) Generation**: A GRN must be recorded in the system within 4 hours of physical receipt. The system automatically creates an `inventory_movement` record of type `purchase_receipt` and increments the location on-hand stock balance.

## 2. Inventory Adjustment & Discrepancy Protocol
- **Shortages / Overages**: Any variance between the PO quantity and physical count exceeding 2% must be flagged to the Category Manager before GRN finalization.
- **Write-Offs & Damaged Goods**: Stock damage resulting in disposal or return to vendor requires a negative adjustment entry with photographic proof attached to the audit ledger.
- **Stock Rotation (FIFO)**: All food and consumable inventory (grains, edible oils, flours, dairy items) must strictly adhere to First-In, First-Out (FIFO) batch movement rules based on receipt date.
