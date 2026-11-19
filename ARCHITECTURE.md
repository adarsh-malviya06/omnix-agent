# OMNIX Agent — System Architecture

OMNIX Agent is an AI-powered enterprise business operations and procurement intelligence system designed specifically for wholesale, distribution, and retail operations.

---

## 1. High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│  Streamlit Multi-Page Enterprise App (App.py + 8 Domain Pages)        │
│  [Overview] [Inventory] [Suppliers] [Procurement]                     │
│  [AI Assistant] [Analytics] [Activity Logs] [Settings]                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct / HTTP Bridge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      MULTI-AGENT ORCHESTRATION                         │
│                           (LangGraph)                                  │
│                                                                        │
│  [User Message] ──► [Business Relevance Guardrail]                     │
│                            │                                           │
│                     (Pass Through)                                     │
│                            ▼                                           │
│                 [Supervisor Agent (Node)]                              │
│                            │                                           │
│         ┌──────────────────┼──────────────────┐                        │
│         ▼                  ▼                  ▼                        │
│  [Inventory Agent]  [Supplier Agent]  [Procurement Agent]              │
│    - Stock Audit      - Vendor Rank     - Policy RAG (ChromaDB)        │
│    - Deficit Check    - Multi-Quote     - Deterministic Reorder Eq.    │
│    - ML Forecast      - Lead Time       - Draft Recommendations        │
│         │                  │                  │                        │
│         └──────────────────┼──────────────────┘                        │
│                            ▼                                           │
│             [Supervisor Response Synthesis]                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     INTELLIGENCE SERVICES     │       │       PERSISTENCE LAYER       │
│                               │       │                               │
│ • ML Demand Forecasting       │       │ • SQLite Database (`omnix.db`)│
│   - Scikit-Learn Ridge Reg.   │       │ • SQLAlchemy 2.0 ORM Models   │
│   - Moving Average Baseline   │       │ • Immutable Audit Logs        │
│   - Time Holdout MAE / RMSE   │       │ • Persistent Settings & Alerts│
│                               │       │                               │
│ • RAG Knowledge Retrieval     │       │ • Vector Storage (`chroma_db`)│
│   - ChromaDB Persistent Store │       │   - Embeddings: MiniLM-L6-v2  │
│   - Policy Document Chunks    │       │   - Procurement SOPs & CTRs   │
│   - Grounded Groq LLM Calls   │       │                               │
└───────────────────────────────┘       └───────────────────────────────┘
```

---

## 2. Multi-Agent Workflow (LangGraph)

The Multi-Agent architecture is built as a state machine using **LangGraph**:

1. **Business-Relevance Guardrail**:
   - Executes deterministically *before* agent invocation.
   - Categorizes incoming messages: `GREETING`, `BUSINESS`, `IRRELEVANT`, `ABUSIVE`, `AMBIGUOUS`.
   - Returns immediate, lightweight responses for greetings, insults, or off-topic requests without incurring LLM or database overhead.

2. **Supervisor Agent**:
   - Analyzes user intent via keyword analysis and policy routing.
   - Dynamically formulates an execution plan:
     - Policy inquiries → `[procurement_agent]` (RAG)
     - Inventory inquiries → `[inventory_agent]`
     - Supplier comparisons → `[supplier_agent]`
     - Reorder/replenishment decisions → `[inventory_agent, supplier_agent, procurement_agent]`
     - General questions → direct Groq LLM answer
   - Consolidates structured agent outputs into an executive report.

3. **Specialized Worker Agents**:
   - **Inventory Agent**: Checks live stock positions, queries low-stock thresholds, and triggers ML demand forecasting for specific SKUs.
   - **Supplier Agent**: Queries active supplier products and ranks quotes using a 40/30/30 composite score (40% Price Competitiveness + 30% Lead Time + 30% Historical Reliability).
   - **Procurement Agent**: Queries company procurement policies via ChromaDB RAG, calculates deterministic replenishment quantities, and writes draft purchase recommendations with status `PENDING_APPROVAL`.

---

## 3. Mandatory Human-in-the-Loop Governance

OMNIX strictly enforces non-autonomous purchasing:
- **No autonomous payments or external supplier orders**: The system generates draft purchase recommendations and purchase orders.
- **Human Authorization Gate**: A warehouse manager or admin must explicitly click "Approve" or "Reject" with mandatory comments.
- **Audit Logging**: Every approval, rejection, stock adjustment, and configuration change generates an immutable `AuditLog` record with timestamp, actor identity, and details.
- **Spending Limit Tiers**:
  - Tier 1: Small order auto-validation limit (configured in Settings, default ₹75,000).
  - Tier 2: Standard operational orders requiring single-level authorization.
  - Tier 3: High-value orders (exceeding high-value threshold, default ₹4,00,000) strictly requiring Admin or Manager roles.

---

## 4. Machine Learning & Forecasting Pipeline

Located in `omnix/ml/forecasting_service.py`:
1. **Data Preprocessing**: Extracts continuous daily sales from `DemandHistory`. Automatically handles zero-demand days and fills missing dates.
2. **Time-Based Holdout Evaluation**: Holds out the most recent 7 days of historical consumption.
3. **Model Selection**: Fits a 7-day Rolling Moving Average baseline and a Scikit-Learn Ridge Linear Regression model with lag features (t-1, t-3, t-7, 7-day rolling mean) and calendar signals (day of week).
4. **Metric Reporting**: Evaluates out-of-sample MAE and RMSE; selects the superior model.
5. **Stockout Risk Synthesis**: Projects forward 14 days, accounting for existing on-hand stock and inbound purchase orders to estimate days until depletion.

---

## 5. RAG Knowledge System

Located in `omnix/rag/`:
- **Vector Storage**: ChromaDB Persistent Client (`./chroma_db`).
- **Embedding Model**: Sentence Transformers `all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Document Loading & Chunking**: Markdown loader with frontmatter metadata extraction and character-recursive chunking with 15% overlap.
- **Context Security**: Policy chunks are treated as untrusted reference data with system prompt guards against prompt injection.
- **Grounded LLM**: Groq API (`llama-3.3-70b-versatile`) with temperature 0.1 for high factual adherence. Explicitly indicates when documents are unavailable instead of hallucinating.

---

## 6. Indian Rupee (INR) Standardization

All monetary figures across UI, database, API, and agent reports adhere strictly to Indian numbering and currency conventions:
- Symbol: `₹`
- Code: `INR`
- Grouping: Thousands (3 digits), then Lakhs (2 digits), then Crores (2 digits).
- Utility: Centralized formatting in `omnix/core/currency.py` (`format_inr`, `format_inr_compact`).
