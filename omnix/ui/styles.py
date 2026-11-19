"""
OMNIX Enterprise Design System Stylesheet.
Clean, soft-grey background, crisp white cards, slate typography, subtle blue accents.
"""

CUSTOM_CSS = """
<style>
/* Main app canvas */
.stApp {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header cleanup */
header[data-testid="stHeader"] {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    padding-top: 1.5rem;
}

/* Hide default streamlit branding clutter */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Custom KPI / Metric Cards */
.omnix-kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    margin-bottom: 1rem;
    transition: box-shadow 0.15s ease-in-out;
}

.omnix-kpi-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07);
}

.omnix-kpi-title {
    font-size: 0.825rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.omnix-kpi-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}

.omnix-kpi-sub {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 0.35rem;
}

/* Status Badges */
.badge-success {
    background-color: #DEF7EC;
    color: #03543F;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

.badge-warning {
    background-color: #FEF3C7;
    color: #92400E;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

.badge-danger {
    background-color: #FDE8E8;
    color: #9B1C1C;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

.badge-info {
    background-color: #E1EFFE;
    color: #1E429F;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

/* Card container for tables and forms */
.omnix-panel {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
}

.omnix-panel-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0F172A;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Standard Button Overrides */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    color: #0F172A;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    border-color: #94A3B8;
    background-color: #F1F5F9;
    color: #0F172A;
}

.stButton > button[kind="primary"] {
    background-color: #2563EB;
    border-color: #2563EB;
    color: #FFFFFF;
}

.stButton > button[kind="primary"]:hover {
    background-color: #1D4ED8;
    border-color: #1D4ED8;
    color: #FFFFFF;
}
</style>
"""
