"""
AI Assistant chat page connected to the LangGraph Multi-Agent Orchestrator
and live backend operational state.
"""

import streamlit as st
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_page_header


def render_ai_assistant_page():
    """Render the interactive AI Operations Assistant chat workspace."""
    render_page_header(
        title="AI Operational Assistant",
        subtitle="Conversational interface powered by LangGraph multi-agent coordination (Supervisor, Inventory, Supplier, Procurement)",
    )

    # 1. Initialize conversational state
    if "agent_chat_messages" not in st.session_state:
        st.session_state.agent_chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Hello! I am OMNIX, your Multi-Agent Operations Assistant.**\n\n"
                    "I am connected to your live inventory database, ML demand forecasting models, "
                    "supplier contracts, and procurement policies.\n\n"
                    "You can ask me to:\n"
                    "- *'Which products are at risk of stockout?'*\n"
                    "- *'Compare suppliers for Basmati Rice'* \n"
                    "- *'What is our policy for orders exceeding ₹4,00,000?'*\n"
                    "- *'Generate a purchase recommendation for Sugar 50kg'* \n\n"
                    "How can I assist your operations today?"
                ),
            }
        ]

    # 2. Render Chat Transcript
    for msg in st.session_state.agent_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "trace" in msg and msg["trace"]:
                with st.expander("🛠️ View Agent Execution Trace", expanded=False):
                    for step in msg["trace"]:
                        st.markdown(f"**[{step['agent_name']}]** `{step['action']}`: {step['details']}")

    # 3. Chat Input and Multi-Agent Orchestration
    user_prompt = st.chat_input("Ask OMNIX (e.g. 'Check stock and replenish Basmati Rice' or 'Compare vendors')...")

    if user_prompt:
        # Append User Message
        st.session_state.agent_chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Trigger Multi-Agent Workflow
        with st.chat_message("assistant"):
            with st.spinner("OMNIX Multi-Agent system coordinating (Supervisor, Inventory, Supplier, Procurement)..."):
                try:
                    result = BackendClient.ask_ai_assistant(query=user_prompt)
                    bot_text = result["final_response"]
                    trace_steps = result.get("execution_trace", [])

                    st.markdown(bot_text)

                    if trace_steps:
                        with st.expander("🛠️ View Agent Execution Trace", expanded=False):
                            for step in trace_steps:
                                st.markdown(f"**[{step['agent_name']}]** `{step['action']}`: {step['details']}")

                    # Save in session history
                    st.session_state.agent_chat_messages.append({
                        "role": "assistant",
                        "content": bot_text,
                        "trace": trace_steps,
                    })
                except Exception as e:
                    err_msg = f"Error processing operational request: {str(e)}"
                    st.error(err_msg)
                    st.session_state.agent_chat_messages.append({
                        "role": "assistant",
                        "content": err_msg,
                    })
