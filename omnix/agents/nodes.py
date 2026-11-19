"""
LangGraph nodes representing the specialized agents:
- SupervisorAgent  (intent classification + response synthesis)
- InventoryAgent   (stock audit, low-stock alerts, ML forecast)
- SupplierAgent    (vendor comparison)
- ProcurementAgent (reorder calculation, policy lookup, PO draft)
"""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from omnix.agents.guardrail import classify_message, MessageCategory
from omnix.agents.state import OmnixAgentState
from omnix.agents.tools import (
    tool_check_inventory_stock,
    tool_compare_suppliers,
    tool_calculate_reorder_order,
    tool_generate_purchase_recommendation,
    tool_get_low_stock_alerts,
    tool_get_ml_forecast,
    tool_get_product_info,
    tool_search_procurement_policies,
)
from omnix.core.currency import format_inr
from omnix.db.models import Product
from omnix.db.session import SessionLocal


# ---------------------------------------------------------------------------
# Intent enumeration for the SupervisorAgent
# ---------------------------------------------------------------------------
class _Intent:
    INVENTORY_CHECK = "inventory_check"       # stock levels, low-stock, out-of-stock
    SUPPLIER_COMPARE = "supplier_compare"     # compare vendors, pricing
    PROCUREMENT_FULL = "procurement_full"     # reorder recommendation (inventory→supplier→procurement)
    POLICY_QUESTION = "policy_question"       # RAG policy lookup
    GENERAL_QUESTION = "general_question"     # date, greeting handled by guardrail, general LLM
    PENDING_APPROVALS = "pending_approvals"   # check purchase order / recommendation status
    GREETING = "greeting"
    IRRELEVANT = "irrelevant"


def _classify_intent(query: str) -> str:
    """
    Rule-based intent classifier for the supervisor.
    Returns one of the _Intent constants.
    """
    q = query.lower().strip()

    # Policy / RAG questions
    policy_signals = ["policy", "procedure", "guideline", "sop", "rule",
                      "compliance", "governance", "threshold", "spending limit",
                      "approval limit", "approval policy", "what is our",
                      "what are our", "what's our"]
    if any(s in q for s in policy_signals):
        # If asking about executing a reorder/replenishment scenario, treat as procurement;
        # otherwise, inquiries about spending limits, thresholds, and general purchasing rules are policy questions.
        if ("reorder" in q or "replenish" in q) and not any(lim in q for lim in ["spending limit", "approval limit", "threshold"]):
            return _Intent.PROCUREMENT_FULL
        return _Intent.POLICY_QUESTION

    # Pending approvals / PO status
    approval_signals = ["pending", "approval", "approve", "reject",
                        "purchase order", "po status", "awaiting"]
    if any(s in q for s in approval_signals):
        return _Intent.PENDING_APPROVALS

    # Full procurement pipeline
    procurement_signals = ["reorder", "replenish", "should we order",
                           "what should we buy", "purchase recommendation",
                           "generate recommendation", "need to buy",
                           "shortage", "running out"]
    if any(s in q for s in procurement_signals):
        return _Intent.PROCUREMENT_FULL

    # Supplier comparison
    supplier_signals = ["supplier", "vendor", "compare supplier",
                        "best price", "cheapest", "lead time",
                        "who supplies", "which supplier", "quote"]
    if any(s in q for s in supplier_signals):
        # If also mentions stock/inventory, may need inventory first
        if any(w in q for w in ["stock", "inventory", "low"]):
            return _Intent.PROCUREMENT_FULL
        return _Intent.SUPPLIER_COMPARE

    # Inventory check
    inventory_signals = ["stock", "inventory", "low stock", "out of stock",
                         "warehouse", "stockout", "how many", "units",
                         "quantity", "depleted", "deficit", "available",
                         "risk", "forecast", "predict", "demand"]
    if any(s in q for s in inventory_signals):
        return _Intent.INVENTORY_CHECK

    # Product-name mentions without clear intent → inventory check
    product_names = ["rice", "sugar", "oil", "atta", "flour", "tea",
                     "ghee", "dal", "wheat", "salt", "spice"]
    if any(p in q for p in product_names):
        return _Intent.INVENTORY_CHECK

    # General / ambiguous question
    return _Intent.GENERAL_QUESTION


# ---------------------------------------------------------------------------
# 1. Supervisor Agent Node
# ---------------------------------------------------------------------------
def supervisor_agent_node(state: OmnixAgentState) -> Dict[str, Any]:
    """
    Supervisor Agent: classifies intent, plans which agents to invoke,
    and after they complete, synthesises the final user-facing response.
    """
    trace = list(state.get("execution_trace", []))
    query = state.get("user_query", "")
    loop_count = state.get("loop_count", 0) + 1

    # Safety guardrail: prevent infinite routing loops
    if loop_count > 5:
        return {
            "is_complete": True,
            "final_response": "Operational workflow stopped: maximum supervisor iterations exceeded.",
            "loop_count": loop_count,
        }

    current_step = state.get("current_step", "start")

    # =====================================================================
    # Phase A: Initial Planning & Routing
    # =====================================================================
    if current_step == "start":
        # 1. Run lightweight guardrail
        guard = classify_message(query)
        if guard.response is not None:
            # Greeting / irrelevant / abusive → answer directly, no agents
            trace.append({
                "agent_name": "SupervisorAgent",
                "action": "GUARDRAIL_RESPONSE",
                "details": f"Message classified as {guard.category.value}. Responded directly.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {
                "final_response": guard.response,
                "is_complete": True,
                "current_step": "completed",
                "loop_count": loop_count,
                "execution_trace": trace,
                "plan": [],
            }

        # 2. Classify business intent
        intent = _classify_intent(query)

        # 3. Build execution plan based on intent
        plan: List[str] = []

        if intent == _Intent.INVENTORY_CHECK:
            plan = ["inventory_agent"]
        elif intent == _Intent.SUPPLIER_COMPARE:
            plan = ["supplier_agent"]
        elif intent == _Intent.PROCUREMENT_FULL:
            plan = ["inventory_agent", "supplier_agent", "procurement_agent"]
        elif intent == _Intent.POLICY_QUESTION:
            plan = ["procurement_agent"]  # procurement agent does RAG lookup
        elif intent == _Intent.PENDING_APPROVALS:
            plan = ["inventory_agent"]  # lightweight: just check status
        elif intent == _Intent.GENERAL_QUESTION:
            # Try answering directly with Groq LLM if available
            direct_answer = _try_direct_llm_answer(query)
            if direct_answer:
                trace.append({
                    "agent_name": "SupervisorAgent",
                    "action": "DIRECT_LLM_ANSWER",
                    "details": "General question answered directly via LLM without agent pipeline.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return {
                    "final_response": direct_answer,
                    "is_complete": True,
                    "current_step": "completed",
                    "loop_count": loop_count,
                    "execution_trace": trace,
                    "plan": [],
                }
            # Fallback if no LLM: politely redirect
            trace.append({
                "agent_name": "SupervisorAgent",
                "action": "REDIRECT_TO_BUSINESS",
                "details": "Could not classify as business question; prompted user to clarify.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {
                "final_response": (
                    "I'm not sure I understand that question in the context of business operations. "
                    "Could you rephrase it?\n\n"
                    "I can help with:\n"
                    "- 📦 Inventory levels and stockout risks\n"
                    "- 🚚 Supplier comparisons\n"
                    "- 📑 Purchase recommendations\n"
                    "- 📋 Procurement policies"
                ),
                "is_complete": True,
                "current_step": "completed",
                "loop_count": loop_count,
                "execution_trace": trace,
                "plan": [],
            }

        trace.append({
            "agent_name": "SupervisorAgent",
            "action": "PLAN_EXECUTION_WORKFLOW",
            "details": f"Intent: {intent}. Pipeline: {' → '.join(plan) if plan else 'direct response'}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "plan": plan,
            "current_step": "plan_ready",
            "loop_count": loop_count,
            "execution_trace": trace,
        }

    # =====================================================================
    # Phase B: Final Response Synthesis (after agents complete)
    # =====================================================================
    inv = state.get("inventory_data") or {}
    sup = state.get("supplier_data") or {}
    proc = state.get("procurement_data") or {}
    fore = state.get("forecasting_data") or {}
    policy = state.get("policy_data") or {}

    response_lines = ["### OMNIX Operations Report\n"]

    # Synthesize Inventory findings
    if inv.get("stock_positions"):
        response_lines.append("**📦 Inventory Analysis:**")
        for p in inv["stock_positions"][:5]:
            status_tag = (
                "🚨 OUT OF STOCK" if p.get("is_out_of_stock")
                else ("⚠️ LOW STOCK" if p.get("is_low_stock") else "✅ HEALTHY")
            )
            response_lines.append(
                f"- **{p['product_name']}** (`{p['product_sku']}`): "
                f"{p['quantity_available']} units available "
                f"(On Hand: {p['quantity_on_hand']}, Reserved: {p['quantity_reserved']}) — {status_tag}"
            )
    elif inv.get("low_stock_alerts"):
        response_lines.append("**📦 Stockout Alerts:**")
        for a in inv["low_stock_alerts"][:5]:
            response_lines.append(
                f"- {a['product_name']} (`{a['product_sku']}`): "
                f"{a['quantity_on_hand']} units (Threshold: {a['safety_min']}) — **{a['status']}**"
            )

    # Synthesize ML Forecasting findings
    if fore and isinstance(fore, dict) and "stockout_risk_level" in fore:
        response_lines.append(f"\n**📈 Demand Forecast & Stockout Risk:**")
        response_lines.append(f"- **Risk Level:** `{fore['stockout_risk_level']}`")
        if fore.get("days_until_stockout"):
            response_lines.append(
                f"- **Estimated Depletion:** In **{fore['days_until_stockout']} days** "
                f"(Est. Date: {fore.get('estimated_stockout_date')})"
            )
        response_lines.append(
            f"- **Average Daily Demand:** {fore.get('average_daily_demand')} units/day "
            f"(Model: {fore.get('model_used')})"
        )

    # Synthesize Supplier findings
    if sup and sup.get("quotes"):
        response_lines.append(f"\n**🚚 Supplier Evaluation:**")
        for q in sup["quotes"][:3]:
            marker = "⭐ " if q.get("is_recommended") else ""
            response_lines.append(
                f"- {marker}**{q['supplier_name']}**: "
                f"{format_inr(q['unit_price'])}/unit | "
                f"Lead: {q['lead_days']}d | "
                f"Reliability: {q['reliability_score']}% | "
                f"Score: {q['composite_score']}/100"
            )

    # Synthesize Procurement & Policy findings
    if proc and proc.get("calculation"):
        calc = proc["calculation"]
        rec = proc.get("recommendation", {})
        response_lines.append(f"\n**📑 Procurement Recommendation:**")
        response_lines.append(f"- **Reorder Point:** {calc['calculated_reorder_point']} units")
        response_lines.append(
            f"- **Suggested Purchase:** **{calc['suggested_order_quantity']} units** "
            f"from {calc['best_supplier_name']}"
        )
        response_lines.append(f"- **Estimated Cost:** **{format_inr(calc['estimated_total_cost'])}**")
        response_lines.append(
            f"- **Governance:** {proc.get('spending_policy_tier', 'Standard')}"
        )
        response_lines.append(
            f"- **Status:** ⏳ `PENDING_APPROVAL` — requires human authorization "
            f"(Rec #{rec.get('recommendation_id', 'N/A')})"
        )

    # Synthesize Policy-only findings (RAG)
    if policy and policy.get("has_content") and not proc:
        response_lines.append(f"\n**📋 Policy Information:**")
        for src in policy.get("sources", [])[:2]:
            response_lines.append(f"- **[{src['document_id']}]** {src['title']}")
            # Show a snippet
            content_preview = src["content"][:300]
            response_lines.append(f"  > {content_preview}")
    elif policy and not policy.get("has_content") and not proc:
        response_lines.append(
            "\n*No relevant procurement policy was found in the OMNIX knowledge base "
            "for this inquiry.*"
        )

    # If nothing was collected, provide a helpful fallback
    if len(response_lines) <= 1:
        response_lines.append(
            "No specific data was found for your query. "
            "Please try rephrasing or ask about inventory, suppliers, or procurement."
        )

    final_text = "\n".join(response_lines)

    trace.append({
        "agent_name": "SupervisorAgent",
        "action": "SYNTHESIZE_FINAL_REPORT",
        "details": f"Consolidated outputs from {len(state.get('plan', []))} agent(s).",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "final_response": final_text,
        "is_complete": True,
        "current_step": "completed",
        "loop_count": loop_count,
        "execution_trace": trace,
    }


# ---------------------------------------------------------------------------
# 2. Inventory Agent Node
# ---------------------------------------------------------------------------
def inventory_agent_node(state: OmnixAgentState) -> Dict[str, Any]:
    """
    Inventory Agent: inspects stock levels, checks low-stock alerts,
    and optionally triggers ML forecast for specific products.
    """
    trace = list(state.get("execution_trace", []))
    product_id = state.get("product_id")
    location_id = state.get("location_id")
    sku = state.get("product_sku")

    db: Session = SessionLocal()
    try:
        # Resolve product from natural language query if not explicitly passed
        if not product_id and not sku:
            query_lower = state.get("user_query", "").lower()
            all_prods = db.query(Product).all()
            for p in all_prods:
                p_keywords = p.name.lower().split()
                if any(kw in query_lower for kw in p_keywords if len(kw) > 3):
                    product_id = p.id
                    sku = p.sku
                    break

        if not product_id and sku:
            prod_info = tool_get_product_info(db, sku)
            product_id = prod_info["id"]

        # 1. Check stock levels
        stock_positions = tool_check_inventory_stock(
            db, product_id=product_id, location_id=location_id
        )

        # Infer location_id if missing
        if not location_id and stock_positions:
            location_id = stock_positions[0]["location_id"]

        # 2. Check low stock alerts if general request (no specific product)
        alerts = []
        if not product_id:
            alerts = tool_get_low_stock_alerts(db)

        # 3. Call ML forecasting if specific product and location
        forecast_data = None
        if product_id and location_id:
            try:
                forecast_data = tool_get_ml_forecast(db, product_id, location_id, horizon_days=14)
            except Exception as e:
                forecast_data = {"error": str(e)}

        inv_summary = {
            "stock_positions": stock_positions,
            "low_stock_alerts": alerts,
            "product_id": product_id,
            "location_id": location_id,
            "status": "COMPLETED",
        }

        trace.append({
            "agent_name": "InventoryAgent",
            "action": "AUDIT_STOCK_AND_FORECAST",
            "details": f"Evaluated {len(stock_positions)} stock position(s) and {len(alerts)} alert(s).",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "inventory_data": inv_summary,
            "forecasting_data": forecast_data,
            "execution_trace": trace,
            "current_step": "inventory_complete",
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Supplier Agent Node
# ---------------------------------------------------------------------------
def supplier_agent_node(state: OmnixAgentState) -> Dict[str, Any]:
    """
    Supplier Agent: compares vendor prices, delivery times, and reliability.
    """
    trace = list(state.get("execution_trace", []))
    product_id = state.get("product_id")

    # If product_id was resolved by inventory agent
    if not product_id and state.get("inventory_data"):
        product_id = state["inventory_data"].get("product_id")

    db: Session = SessionLocal()
    try:
        supplier_summary = None
        if product_id:
            supplier_summary = tool_compare_suppliers(db, product_id)
            details = f"Ranked {len(supplier_summary.get('quotes', []))} vendor quotes for Product ID {product_id}."
        else:
            details = "No specific product identified; general supplier query."

        trace.append({
            "agent_name": "SupplierAgent",
            "action": "EVALUATE_AND_RANK_SUPPLIERS",
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "supplier_data": supplier_summary,
            "execution_trace": trace,
            "current_step": "supplier_complete",
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. Procurement Agent Node
# ---------------------------------------------------------------------------
def procurement_agent_node(state: OmnixAgentState) -> Dict[str, Any]:
    """
    Procurement Agent: retrieves policy via RAG, calculates reorder,
    and creates pending recommendation entries.
    """
    trace = list(state.get("execution_trace", []))
    product_id = state.get("product_id")
    location_id = state.get("location_id")
    user_query = state.get("user_query", "")

    if not product_id and state.get("inventory_data"):
        product_id = state["inventory_data"].get("product_id")
    if not location_id and state.get("inventory_data"):
        location_id = state["inventory_data"].get("location_id")

    db: Session = SessionLocal()
    try:
        # 1. Search policies using RAG (use user query for better relevance)
        policy_query = user_query if user_query else "spending limits approval threshold and reorder policy"
        policies = tool_search_procurement_policies(policy_query)

        # 2. Calculate deterministic reorder recommendation (only if product context available)
        proc_data = None
        if product_id and location_id:
            reorder_calc = tool_calculate_reorder_order(db, product_id, location_id)
            rec_entry = tool_generate_purchase_recommendation(db, product_id, location_id)
            proc_data = {
                "calculation": reorder_calc,
                "recommendation": rec_entry,
                "spending_policy_tier": (
                    "Tier 2 — Operational Reorder (Up to ₹75,000)"
                    if reorder_calc["estimated_total_cost"] <= 75000
                    else "Tier 3 — Substantial Orders (Above ₹75,000)"
                ),
                "requires_human_approval": True,
            }
            details = (
                f"Generated reorder for Product {product_id}. "
                f"Qty: {reorder_calc['suggested_order_quantity']}, "
                f"Cost: {format_inr(reorder_calc['estimated_total_cost'])}. PENDING_APPROVAL."
            )
        else:
            details = "Retrieved procurement policies; no specific product context for order calculation."

        trace.append({
            "agent_name": "ProcurementAgent",
            "action": "CALCULATE_REORDER_AND_CHECK_POLICIES",
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "policy_data": policies,
            "procurement_data": proc_data,
            "execution_trace": trace,
            "current_step": "procurement_complete",
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper: Direct LLM answer for general questions
# ---------------------------------------------------------------------------
def _try_direct_llm_answer(query: str) -> Optional[str]:
    """
    Attempt to answer a general (non-business) question using Groq LLM directly.
    Returns None if Groq is unavailable.
    """
    try:
        from omnix.core.config import get_settings
        settings = get_settings()
        if not settings.groq_api_key:
            return None

        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are OMNIX, a business operations assistant for inventory, "
                        "suppliers, and procurement. Answer the user's question briefly "
                        "and helpfully. If the question is unrelated to business operations, "
                        "answer it briefly but remind the user you're primarily here for "
                        "business operations support."
                    ),
                },
                {"role": "user", "content": query},
            ],
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None
