"""
Tests for the Business-Relevance Guardrail and Intent Classification.
"""

import pytest
from omnix.agents.guardrail import classify_message, MessageCategory


class TestGuardrail:
    """Tests for classify_message()."""

    # --- Greetings ---
    @pytest.mark.parametrize("text", [
        "Hello",
        "Hi",
        "Hey",
        "Good morning",
        "Good afternoon",
        "Howdy",
        "Namaste",
    ])
    def test_greeting_detected(self, text):
        result = classify_message(text)
        assert result.category == MessageCategory.GREETING
        assert result.response is not None
        assert "OMNIX" in result.response

    # --- Business questions pass through ---
    @pytest.mark.parametrize("text", [
        "Which products are running low on stock?",
        "Compare suppliers for rice",
        "What is our spending approval policy?",
        "Show me inventory levels",
        "What should we reorder?",
        "How many units of sugar do we have?",
        "What is the procurement procedure?",
        "Is rice stock running low?",
        "Forecast demand for ghee",
        "What are the pending purchase approvals?",
    ])
    def test_business_question_passes(self, text):
        result = classify_message(text)
        assert result.category == MessageCategory.BUSINESS
        assert result.response is None  # No pre-canned response — goes to agents

    # --- Irrelevant messages ---
    @pytest.mark.parametrize("text", [
        "Tell me a joke",
        "Sing a song",
        "Write a poem",
        "Who is the president",
        "What is the meaning of life",
    ])
    def test_irrelevant_detected(self, text):
        result = classify_message(text)
        assert result.category == MessageCategory.IRRELEVANT
        assert result.response is not None

    # --- Abusive messages ---
    @pytest.mark.parametrize("text", [
        "You are stupid",
        "This is useless garbage",
        "What a dumb system",
    ])
    def test_abusive_detected(self, text):
        result = classify_message(text)
        assert result.category == MessageCategory.ABUSIVE
        assert result.response is not None
        assert "professional" in result.response.lower()

    # --- Abusive BUT also business → allow through ---
    def test_abusive_with_business_keyword_passes(self):
        result = classify_message("This stupid system won't show my inventory")
        assert result.category == MessageCategory.BUSINESS
        assert result.response is None

    # --- Ambiguous questions → let agents handle ---
    @pytest.mark.parametrize("text", [
        "What is today's date?",
        "Can you help me with something?",
        "I need some information about operations",
    ])
    def test_ambiguous_passes_through(self, text):
        result = classify_message(text)
        # Either BUSINESS or AMBIGUOUS, but NOT IRRELEVANT
        assert result.category in (MessageCategory.BUSINESS, MessageCategory.AMBIGUOUS)

    # --- Empty input ---
    def test_empty_input(self):
        result = classify_message("")
        assert result.category == MessageCategory.AMBIGUOUS
        assert result.response is not None

    def test_whitespace_only(self):
        result = classify_message("   ")
        assert result.category == MessageCategory.AMBIGUOUS


class TestIntentClassification:
    """Tests for _classify_intent() in nodes.py."""

    def test_policy_question(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("What is our procurement policy?") == _Intent.POLICY_QUESTION

    def test_spending_limit_policy(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("What is our spending limit for purchases?") == _Intent.POLICY_QUESTION

    def test_inventory_check(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("How much rice stock do we have?") == _Intent.INVENTORY_CHECK

    def test_supplier_compare(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("Compare suppliers for rice") == _Intent.SUPPLIER_COMPARE

    def test_reorder_triggers_procurement(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("Should we reorder sugar?") == _Intent.PROCUREMENT_FULL

    def test_general_question(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("What is today's date?") == _Intent.GENERAL_QUESTION

    def test_pending_approvals(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("What are the pending approvals?") == _Intent.PENDING_APPROVALS

    def test_forecast_is_inventory(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        assert _classify_intent("Forecast demand for ghee") == _Intent.INVENTORY_CHECK

    def test_policy_with_order_is_procurement(self):
        from omnix.agents.nodes import _classify_intent, _Intent
        result = _classify_intent("What is the policy for reorder purchases above 4 lakhs?")
        assert result == _Intent.PROCUREMENT_FULL
