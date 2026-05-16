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


_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 นาที


def require_pin() -> bool:
    """Show PIN gate with rate limiting. Returns True if authenticated."""
    import time

    if st.session_state.get("pin_ok"):
        return True

    # ── Rate limit check ──────────────────────────────────────────────
    attempts = st.session_state.get("pin_attempts", 0)
    locked_until = st.session_state.get("pin_locked_until", 0)
    now = time.time()

    if locked_until > now:
        remaining = int(locked_until - now)
        mins, secs = divmod(remaining, 60)
        st.markdown(f"""
        <div style="max-width:340px; margin:3rem auto; background:#2A1A1A;
                    border:1px solid #E53935; border-radius:14px; padding:2rem; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🚫</div>
            <div style="font-size:1.1rem; font-weight:600; color:#EF5350; margin-bottom:0.5rem;">
                ล็อคชั่วคราว
            </div>
            <div style="font-size:0.9rem; color:#FFCDD2;">
                ใส่ PIN ผิดหลายครั้ง<br>รอ <b>{mins}:{secs:02d}</b> นาที
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.rerun()
        return False

    try:
        correct_pin = str(st.secrets["auth"]["PIN"]).strip()
    except Exception:
        correct_pin = "1234"

    attempts_left = _MAX_ATTEMPTS - attempts
    st.markdown(f"""
    <div style="max-width:340px; margin:3rem auto; background:#1A1F2E;
                border:1px solid #2A3040; border-radius:14px; padding:2rem; text-align:center;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔐</div>
        <div style="font-size:1.1rem; font-weight:600; color:#4FC3F7; margin-bottom:0.25rem;">
            ต้องใส่ PIN เพื่อแก้ไขข้อมูล
        </div>
        <div style="font-size:0.8rem; color:#888; margin-bottom:1.5rem;">
            {"ดูข้อมูลได้ที่หน้า Dashboard" if attempts == 0 else f"⚠️ เหลือ {attempts_left} ครั้ง ก่อนล็อค 5 นาที"}
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
                st.session_state["pin_attempts"] = 0
                st.rerun()
            else:
                new_attempts = attempts + 1
                st.session_state["pin_attempts"] = new_attempts
                if new_attempts >= _MAX_ATTEMPTS:
                    st.session_state["pin_locked_until"] = now + _LOCKOUT_SECONDS
                    st.session_state["pin_attempts"] = 0
                    st.rerun()
                else:
                    st.error(f"PIN ไม่ถูกต้อง — เหลือ {_MAX_ATTEMPTS - new_attempts} ครั้ง")

    return False


def require_user() -> str | None:
    """After PIN, ask who is logged in. Returns username or None."""
    if not st.session_state.get("pin_ok"):
        return None
    if st.session_state.get("current_user"):
        return st.session_state["current_user"]

    from sheets import get_staff_list
    staff = get_staff_list()

    st.markdown("""
    <div style="max-width:340px; margin:2rem auto; background:#1A1F2E;
                border:1px solid #2A3040; border-radius:14px; padding:2rem; text-align:center;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">👤</div>
        <div style="font-size:1.1rem; font-weight:600; color:#4FC3F7; margin-bottom:0.5rem;">
            คุณคือใคร?
        </div>
        <div style="font-size:0.8rem; color:#888;">เลือกชื่อเพื่อเริ่มบันทึก</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        for name in staff:
            if st.button(name, use_container_width=True, key=f"login_{name}"):
                st.session_state["current_user"] = name
                st.rerun()

    return None


def get_current_user() -> str:
    return st.session_state.get("current_user", "unknown")


def pin_logout_button():
    """Sidebar: show current user + logout button."""
    if st.session_state.get("pin_ok"):
        user = st.session_state.get("current_user")
        if user:
            st.sidebar.markdown(f"**👤 {user}**")
        if st.sidebar.button("🔒 ล็อกออก", use_container_width=True):
            st.session_state["pin_ok"] = False
            st.session_state["current_user"] = None
            st.rerun()
