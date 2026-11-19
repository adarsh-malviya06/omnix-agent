# OMNIX Agent
## Multi-Agent Procurement & Inventory Intelligence Platform

OMNIX Agent is an AI-powered enterprise business operations platform designed for wholesale, distribution, retail stores, and supermarkets. It unifies inventory tracking, demand forecasting, supplier evaluation, and procurement policies through a Supervisor-coordinated Multi-Agent architecture with mandatory human-in-the-loop authorization.

All user-facing monetary values are expressed in **Indian Rupees (INR, ₹)** with standard Indian number formatting (lakhs and crores, e.g. `₹1,25,000.00`).

---

## 🌟 Core Features

- **Operations Dashboard**: Real-time business KPIs (Total Products, Live Inventory Valuation, Low-Stock SKUs, Out of Stock Depletions, Pending Approvals, Active Purchase Orders).
- **Multi-Agent AI Assistant**: Powered by LangGraph (Supervisor, Inventory, Supplier, Procurement agents) with business-relevance guardrails, direct conversational answers, and execution traces.
- **Inventory Intelligence & Persistent Alerts**: Real-time stock audit, deficit detection, safety threshold calculations, and persistent warning alerts with one-click resolution.
- **ML Demand Forecasting**: Time-series demand prediction using Scikit-Learn Ridge Regression with lag features, Rolling Moving Average baseline, and out-of-sample holdout evaluation (MAE & RMSE).
- **Supplier Ranking & Evaluation**: Multi-attribute quote scoring (40% Price + 30% Lead Time + 30% Reliability) across approved supplier networks.
- **RAG Policy Knowledge**: ChromaDB vector store with `all-MiniLM-L6-v2` embeddings and Groq LLM inference (`llama-3.3-70b-versatile`) answering procurement questions with verified citations.
- **Human-in-the-Loop Procurement**: Pending recommendation review gate with approve/reject workflows and immutable audit logs.
- **Persistent Settings & Governance**: Configurable spending limits and safety buffers persisted in the database across application restarts.

---

## 🏗️ System Architecture

Refer to [ARCHITECTURE.md](file:///c:/Users/User/OneDrive/Desktop/omnix-agent/ARCHITECTURE.md) for full architectural design and diagrams.
Refer to [DATABASE_SCHEMA.md](file:///c:/Users/User/OneDrive/Desktop/omnix-agent/DATABASE_SCHEMA.md) for database tables, relationships, and constraints.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/your-org/omnix-agent.git
cd omnix-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Database and Seed Demo Data

Run the database seeder to initialize all relational tables and load realistic wholesale/retail demo data:
```bash
python -m omnix.db.seed
```

This populates:
- Wholesale and retail organization profiles
- Facilities and warehouses
- Master product catalog with SKUs (Basmati Rice, Sugar, Sunflower Oil, Atta, Tea, Ghee, Toor Dal, Mustard Oil)
- On-hand stock positions and inventory valuation
- Historical daily consumption records for ML training
- Approved suppliers, vendor quotes, and commercial terms
- Initial pending recommendations and purchase orders

### 5. Launch the Application

#### Streamlit Frontend Dashboard (Default Port 8501)
```bash
python -m streamlit run omnix/ui/app.py --server.port 8501
```
Open your browser at [http://localhost:8501](http://localhost:8501).

The application provides 8 operational screens via sidebar navigation:
1. **Operations Overview**: Real-time KPIs, active alerts, live inventory positions, and active purchase orders.
2. **Inventory Management**: Searchable SKU catalog, category filters, and safety threshold auditing.
3. **Supplier Network**: Vendor performance ratings and multi-attribute quote comparison tool.
4. **Procurement & POs**: Human authorization gate for AI recommendations and master purchase order registry.
5. **AI Assistant**: Conversational operations interface with LangGraph multi-agent execution traces.
6. **Business Analytics**: Database-backed demand trends, Scikit-Learn predictive modeling metrics, and vendor spend breakdown.
7. **Activity Logs**: Immutable compliance audit trail tracking approvals, rejections, and inventory adjustments.
8. **Settings & Governance**: Configurable spending thresholds and safety buffers with database persistence.

#### FastAPI Backend Service (Default Port 8000)
```bash
uvicorn omnix.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Health Status: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Interactive OpenAPI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing

Execute automated unit and integration tests:

```bash
# Run full test suite
python -m pytest -v

# Run targeted test suites
python -m pytest tests/test_guardrail.py -v
python -m pytest tests/test_settings.py -v
python -m pytest tests/test_alerts.py -v
python -m pytest tests/test_analytics.py -v
python -m pytest tests/test_ui_pages.py -v
```

---

## 🔒 Security & Compliance

- **No Secrets in Source**: `.env` and SQLite databases (`*.db`) are ignored in `.gitignore`.
- **Untrusted RAG Context**: Retrieved policy document excerpts are treated strictly as passive context with prompt injection defenses.
- **Non-Autonomous Purchasing**: Purchase orders require explicit human sign-off; no autonomous real-world payments occur.
- **Audit Logging**: Every approval, rejection, and threshold change records an immutable `AuditLog` entry.
