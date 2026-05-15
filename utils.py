import streamlit as st

_CSS = """
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #4FC3F7; margin-bottom: 0.25rem; }
    .sub-header  { font-size: 0.9rem; color: #888; margin-bottom: 1.5rem; }
    [data-testid="metric-container"] {
        background-color: #1A1F2E; border: 1px solid #2A3040; border-radius: 12px; padding: 1rem;
    }
    .alert-box {
        background-color: #2A1A1A; border-left: 4px solid #FF5252;
        border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem;
    }
    .alert-title { color: #FF5252; font-weight: 600; font-size: 1rem; margin-bottom: 0.5rem; }
    .alert-item  { color: #FFCDD2; font-size: 0.9rem; padding: 0.15rem 0; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #4FC3F7;
        border-bottom: 1px solid #2A3040; padding-bottom: 0.4rem; margin-bottom: 0.75rem;
    }
    .staff-label { font-size: 0.85rem; color: #888; margin-bottom: 0.5rem; }
    .check-ok   { background:#1B2E1B; border:1px solid #388E3C; border-radius:8px; padding:0.5rem 0.75rem; text-align:center; font-size:0.8rem; color:#A5D6A7; }
    .check-warn { background:#2A2000; border:1px solid #F9A825; border-radius:8px; padding:0.5rem 0.75rem; text-align:center; font-size:0.8rem; color:#FFE082; }
    .check-late { background:#2A1A1A; border:1px solid #E53935; border-radius:8px; padding:0.5rem 0.75rem; text-align:center; font-size:0.8rem; color:#EF9A9A; }
    .check-none { background:#1A1F2E; border:1px solid #37474F; border-radius:8px; padding:0.5rem 0.75rem; text-align:center; font-size:0.8rem; color:#607D8B; }
    hr { border-color: #2A3040 !important; }
    [data-testid="stDataFrame"] { border: 1px solid #2A3040; border-radius: 10px; overflow: hidden; }
    .badge-in  { color: #66BB6A; font-weight: 600; }
    .badge-out { color: #E57373; font-weight: 600; }
</style>
"""


def apply_styles():
    st.markdown(_CSS, unsafe_allow_html=True)
