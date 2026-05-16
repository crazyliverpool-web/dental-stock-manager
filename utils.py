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

    /* ── Mobile (≤768px) ─────────────────────────────────────────── */
    @media (max-width: 768px) {
        .main-header { font-size: 1.4rem !important; }
        .sub-header  { font-size: 0.8rem !important; margin-bottom: 0.75rem !important; }
        .section-title { font-size: 0.95rem !important; }

        /* ปุ่มใหญ่ขึ้น กดง่ายบนมือถือ */
        .stButton > button {
            min-height: 3rem !important;
            font-size: 1rem !important;
            padding: 0.5rem 0.75rem !important;
        }

        /* columns wrap แทนที่จะล้นออกหน้าจอ */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.4rem !important;
        }
        [data-testid="stHorizontalBlock"] > div {
            min-width: 72px !important;
            flex: 1 1 72px !important;
        }

        /* check status cards เล็กลงนิด */
        .check-ok, .check-warn, .check-late, .check-none {
            font-size: 0.72rem !important;
            padding: 0.4rem 0.4rem !important;
        }

        /* metric cards padding ลด */
        [data-testid="metric-container"] { padding: 0.6rem !important; }

        /* table font เล็กลงให้อ่านได้บนมือถือ */
        [data-testid="stDataFrame"] td,
        [data-testid="stDataFrame"] th { font-size: 0.78rem !important; }

        /* sidebar collapse ให้พื้นที่หน้าหลัก */
        [data-testid="stSidebar"] { min-width: 0 !important; }
    }

    /* ── Tablet (769–1024px) ─────────────────────────────────────── */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main-header { font-size: 1.6rem !important; }
        .stButton > button { min-height: 2.5rem !important; font-size: 0.95rem !important; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.3rem !important; }
        [data-testid="stHorizontalBlock"] > div { min-width: 80px !important; flex: 1 1 80px !important; }
    }
</style>
"""


def apply_styles():
    st.markdown(_CSS, unsafe_allow_html=True)


def require_pin() -> bool:
    """Show PIN gate. Returns True if already authenticated, False and renders form if not."""
    if st.session_state.get("pin_ok"):
        return True

    try:
        correct_pin = str(st.secrets["auth"]["PIN"]).strip()
    except Exception:
        correct_pin = "1234"

    st.markdown("""
    <div style="max-width:340px; margin:3rem auto; background:#1A1F2E;
                border:1px solid #2A3040; border-radius:14px; padding:2rem; text-align:center;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔐</div>
        <div style="font-size:1.1rem; font-weight:600; color:#4FC3F7; margin-bottom:0.25rem;">
            ต้องใส่ PIN เพื่อแก้ไขข้อมูล
        </div>
        <div style="font-size:0.8rem; color:#888; margin-bottom:1.5rem;">
            หน้านี้ป้องกันด้วย PIN — ดูข้อมูลได้ที่หน้า Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("pin_form", clear_on_submit=True):
            entered = st.text_input("PIN", type="password", placeholder="ใส่ PIN แล้วกด Enter",
                                    label_visibility="collapsed")
            submitted = st.form_submit_button("ปลดล็อก", type="primary", use_container_width=True)

        if submitted:
            if entered.strip() == correct_pin:
                st.session_state["pin_ok"] = True
                st.rerun()
            else:
                st.error("PIN ไม่ถูกต้อง")

    return False


def pin_logout_button():
    """Small lock button in sidebar to end the PIN session."""
    if st.session_state.get("pin_ok"):
        if st.sidebar.button("🔒 ล็อคระบบ", use_container_width=True):
            st.session_state["pin_ok"] = False
            st.rerun()
