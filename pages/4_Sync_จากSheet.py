import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import sync_from_check_sheet
from utils import apply_styles, require_pin, require_user, pin_logout_button

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

if st.button("🔁 Sync ตอนนี้เลย", type="primary", use_container_width=False):
    with st.spinner("กำลัง sync..."):
        result = sync_from_check_sheet()

    st.success(f"✅ Sync สำเร็จ!")

    col1, col2, col3 = st.columns(3)
    col1.metric("จับคู่ได้", result["matched"])
    col2.metric("ตัวเลขเปลี่ยน", result["updated"])
    col3.metric("ข้ามไป", result["skipped"])

    if result["updated"] > 0:
        changed = [d for d in result["details"] if d["เปลี่ยน"]]
        st.markdown("#### รายการที่ตัวเลขเปลี่ยน")
        for d in changed:
            st.markdown(f"- **{d['ชื่อ']}**: {d['เดิม']} → **{d['ใหม่']}**")

    if result["skipped_names"]:
        with st.expander(f"รายการที่ข้ามไป ({result['skipped']} รายการ)"):
            for name in result["skipped_names"]:
                st.markdown(f"- {name}")
