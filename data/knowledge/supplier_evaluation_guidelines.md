# Supplier Evaluation, Selection Criteria, and On-Time Delivery Guidelines
Document ID: POL-SUP-003
Category: Supplier Evaluation
Version: 1.1
Applies To: Vendor Management Desk

## 1. Multi-Attribute Evaluation Framework
Supplier selection for procurement replenishment is governed by a transparent, quantitative scoring model. Purchasing decisions must not rely exclusively on the lowest quoted unit rate.

### Scoring Dimensions:
1. **Pricing Competitiveness (40% Weight)**:
   - Evaluated as the ratio of the lowest market quote to the vendor's quoted price:
     Price Score = (Lowest Market Price / Vendor Quoted Price) * 100.
2. **Delivery Speed & Lead Time (30% Weight)**:
   - Evaluated relative to the fastest available delivery timeframe in the network:
     Lead Time Score = (Fastest Lead Days / Vendor Lead Days) * 100.
3. **Historical Reliability Score (30% Weight)**:
   - Derived from the rolling 12-month on-time, in-full (OTIF) delivery track record maintained in the supplier master table (0.0% to 100.0%).

## 2. Supplier Categorization & Disqualification Rules
- **Preferred Vendor Tier**: Reliability score >= 90.0% with minimum 10 successful dispatches in the trailing 6 months.
- **Probationary Tier**: Reliability score between 75.0% and 89.9%. Allowed for backup fulfillment only.
- **Disqualified / Blocked Tier**: Vendors with reliability scores below 75.0% or 3 consecutive quality rejections are automatically suspended from receiving automated purchase recommendations until recertified by the Operations Director.
