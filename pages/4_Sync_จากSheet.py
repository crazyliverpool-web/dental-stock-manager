import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import preview_sync_from_check_sheet, sync_from_check_sheet
from utils import apply_styles, require_pin, require_user, get_current_user, pin_logout_button

st.set_page_config(page_title="Sync จาก Sheet เช็คสต๊อก", page_icon="🔁", layout="wide")
apply_styles()
pin_logout_button()

if not require_pin():
    st.stop()

if not require_user():
    st.stop()

st.markdown('<div class="main-header">🔁 Sync จาก Sheet เช็คสต๊อกรายเดือน</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ดึงจำนวนคงเหลือล่าสุดจาก Sheet ของแต่ละพนักงานมาอัพเดทใน Stock</div>',
            unsafe_allow_html=True)
st.info("📋 ดึงข้อมูลจาก **เช็คสต๊อกรายเดือน เเต่ละบุคคล** — อินอาร์ม, พี่เปิ้ล, ฮัน, ฟีร่า, กะมี, อิสสะห์, ดารณี")
st.divider()

# ─── Step 1: Preview ──────────────────────────────────────────────────────────
if "sync_preview" not in st.session_state:
    st.session_state.sync_preview = None

if st.session_state.sync_preview is None:
    if st.button("🔍 ดูตัวอย่างก่อน Sync", type="primary", use_container_width=False):
        with st.spinner("กำลังโหลดตัวอย่าง..."):
            st.session_state.sync_preview = preview_sync_from_check_sheet()
        st.rerun()

# ─── Step 2: Show preview + confirm ──────────────────────────────────────────
else:
    result = st.session_state.sync_preview
    changed = [d for d in result["details"] if d["เปลี่ยน"]]

    st.markdown('<div class="section-title">📋 ตัวอย่างการเปลี่ยนแปลง</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("จับคู่ได้", result["matched"])
    col2.metric("ตัวเลขจะเปลี่ยน", result["updated"])
    col3.metric("ข้ามไป", result["skipped"])

    if changed:
        st.markdown("**รายการที่จะถูกอัพเดท:**")
        for d in changed:
            arrow = "🔺" if d["ใหม่"] > d["เดิม"] else "🔻"
            st.markdown(f"- {d['ชื่อ']}: **{d['เดิม']}** → **{d['ใหม่']}** {arrow}")
    else:
        st.success("ตัวเลขทุกรายการตรงกันอยู่แล้ว ไม่มีอะไรเปลี่ยน")

    if result["skipped_names"]:
        with st.expander(f"รายการที่จับคู่ไม่ได้ ({result['skipped']} รายการ)"):
            for name in result["skipped_names"]:
                st.markdown(f"- {name}")

    st.divider()
    confirm_col, cancel_col = st.columns([1, 1], gap="large")

    with confirm_col:
        if st.button("✅ ยืนยัน Sync เลย", type="primary", use_container_width=True,
                     disabled=result["updated"] == 0):
            with st.spinner("กำลัง sync..."):
                final = sync_from_check_sheet()
            st.session_state.sync_preview = None
            st.success(f"✅ Sync สำเร็จ — อัพเดท {final['updated']} รายการ")

    with cancel_col:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.session_state.sync_preview = None
            st.rerun()
