"""
Activity logs and audit trails page connected to real database audit events.
"""

import pandas as pd
import streamlit as st
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_page_header


def render_activity_logs_page():
    """Render the Activity Logs & Audit Trail view using real database audit entries."""
    render_page_header(
        title="Activity & Governance Logs",
        subtitle="Immutable audit trail of automated agent decisions, user approvals, and stock movements",
    )

    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">System Audit Log Entries</div>', unsafe_allow_html=True)

    logs = BackendClient.get_audit_logs_table(limit=100)
    if logs:
        log_df = pd.DataFrame(logs)
        st.dataframe(
            log_df[["timestamp", "actor", "event_type", "action", "details"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Timestamp (UTC)",
                "actor": "Actor / User",
                "event_type": "Event Category",
                "action": "Action Event",
                "details": "Audit Context & Metadata",
            },
        )
    else:
        st.info("No audit logs found.")

    st.markdown("</div>", unsafe_allow_html=True)
