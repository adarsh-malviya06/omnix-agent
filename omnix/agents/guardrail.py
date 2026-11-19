"""
Business-relevance guardrail for OMNIX Agent.

Lightweight keyword-based classifier that runs BEFORE the SupervisorAgent
to quickly categorise user messages without expensive LLM calls.

Categories:
  - BUSINESS:    Legitimate inventory / supplier / procurement / policy question
  - GREETING:    Hello, hi, good morning, etc.
  - IRRELEVANT:  Jokes, trivia, off-topic entertainment
  - ABUSIVE:     Profanity or insults directed at the system
  - AMBIGUOUS:   Cannot confidently classify
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MessageCategory(str, Enum):
    BUSINESS = "BUSINESS"
    GREETING = "GREETING"
    IRRELEVANT = "IRRELEVANT"
    ABUSIVE = "ABUSIVE"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class GuardrailResult:
    category: MessageCategory
    response: Optional[str]  # Pre-canned response (None → continue to agents)


# ---------------------------------------------------------------------------
# Keyword / pattern banks
# ---------------------------------------------------------------------------

_GREETING_PATTERNS = re.compile(
    r"^(h(ello|i|ey)|good\s*(morning|afternoon|evening|day)|"
    r"what'?s?\s*up|howdy|greetings|namaste|yo|sup)\b",
    re.IGNORECASE,
)

_ABUSIVE_WORDS = {
    "stupid", "idiot", "dumb", "trash", "useless", "garbage", "suck",
    "moron", "fool", "pathetic", "worthless", "crap",
}

_IRRELEVANT_SIGNALS = [
    "tell me a joke", "sing a song", "write a poem", "tell me a story",
    "play a game", "who is the president", "what is the meaning of life",
    "how old are you", "are you alive", "what is love",
    "who won the match", "movie recommendation", "recipe for",
    "capital of", "translate this", "write code for",
    "solve this math", "help me cheat",
]

_BUSINESS_KEYWORDS = [
    # Inventory
    "stock", "inventory", "warehouse", "low stock", "out of stock",
    "restock", "stockout", "units", "quantity", "sku", "product",
    "goods", "replenish", "deficit", "surplus", "safety stock",
    "reorder", "reorder point",
    # Supplier
    "supplier", "vendor", "quote", "lead time",
    "reliability", "contract", "agreement", "moq", "minimum order",
    # Procurement
    "purchase order", "procurement", "cost",
    "spending", "budget", "approval", "approve", "reject",
    "recommendation", "pending",
    # Policy / RAG
    "policy", "procedure", "guideline", "sop",
    "threshold", "limit", "compliance", "governance", "audit",
    # Forecasting / Analytics
    "forecast", "predict", "demand", "trend", "risk", "analytics",
    "report", "dashboard", "kpi", "metric",
    # Domain products
    "rice", "sugar", "oil", "atta", "flour", "tea", "ghee",
    "dal", "wheat", "salt", "spice",
]


def classify_message(text: str) -> GuardrailResult:
    """
    Classify a user message into a business-relevance category.

    This is intentionally a lightweight keyword classifier — no LLM call.
    It errs on the side of allowing messages through (AMBIGUOUS → agents).
    """
    if not text or not text.strip():
        return GuardrailResult(
            category=MessageCategory.AMBIGUOUS,
            response="Could you please type your question? I'm here to help with inventory, suppliers, and procurement.",
        )

    cleaned = text.strip()
    lower = cleaned.lower()

    # 1. Very short greeting check
    if len(cleaned.split()) <= 4 and _GREETING_PATTERNS.match(lower):
        return GuardrailResult(
            category=MessageCategory.GREETING,
            response=(
                "Hello! 👋 I'm **OMNIX**, your business operations assistant.\n\n"
                "I can help you with:\n"
                "- 📦 Inventory levels and stockout risks\n"
                "- 🚚 Supplier comparisons and pricing\n"
                "- 📑 Purchase recommendations and approvals\n"
                "- 📋 Procurement policies and procedures\n\n"
                "What would you like to know?"
            ),
        )

    # 2. Abusive language check (but allow if also contains business keywords)
    words_in_message = set(re.findall(r"\w+", lower))
    has_abuse = bool(words_in_message & _ABUSIVE_WORDS)
    has_business = any(kw in lower for kw in _BUSINESS_KEYWORDS)

    if has_abuse and not has_business:
        return GuardrailResult(
            category=MessageCategory.ABUSIVE,
            response=(
                "Let's keep things professional. I'm here to assist with your "
                "business operations — inventory, suppliers, and procurement. "
                "How can I help?"
            ),
        )

    # 3. Business keyword match — allow through
    if has_business:
        return GuardrailResult(category=MessageCategory.BUSINESS, response=None)

    # 4. Irrelevant pattern check
    if any(signal in lower for signal in _IRRELEVANT_SIGNALS):
        return GuardrailResult(
            category=MessageCategory.IRRELEVANT,
            response=(
                "I'm focused on business operations — inventory management, "
                "supplier analysis, and procurement workflows. "
                "Let's keep our conversation relevant to OMNIX! 😊\n\n"
                "Try asking something like:\n"
                "- *'Which products are running low?'*\n"
                "- *'Compare suppliers for rice'*\n"
                "- *'What is our spending approval policy?'*"
            ),
        )

    # 5. If the message is a question (contains ?) or reasonably long,
    #    give it the benefit of the doubt → AMBIGUOUS → let agents handle
    if "?" in cleaned or len(cleaned.split()) >= 4:
        return GuardrailResult(category=MessageCategory.AMBIGUOUS, response=None)

    # 6. Very short non-business, non-greeting message
    return GuardrailResult(
        category=MessageCategory.IRRELEVANT,
        response=(
            "I'm here to help with business operations — inventory, "
            "suppliers, and procurement. Could you rephrase your question?"
        ),
    )
