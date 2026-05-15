import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import date
from sheets import get_stock_df, save_stock_updates, record_stock_check, get_staff_list
from utils import apply_styles

STAFF = get_staff_list()

st.set_page_config(page_title="อัพเดทสต้อค", page_icon="📋", layout="wide")
apply_styles()

st.markdown('<div class="main-header">📋 อัพเดทสต้อค</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">นับของแล้วใส่ตัวเลข กดบันทึกครั้งเดียว</div>', unsafe_allow_html=True)

# ─── Staff selector ───────────────────────────────────────────────────────────
st.markdown('<div class="staff-label">👤 เลือกพนักงาน</div>', unsafe_allow_html=True)

if "selected_staff_form" not in st.session_state:
    st.session_state.selected_staff_form = "ทั้งหมด"

btn_cols = st.columns(len(STAFF) + 1)
for i, name in enumerate(["ทั้งหมด"] + STAFF):
    btn_type = "primary" if st.session_state.selected_staff_form == name else "secondary"
    if btn_cols[i].button(name, key=f"fs_{name}", type=btn_type, use_container_width=True):
        st.session_state.selected_staff_form = name
        st.rerun()

selected = st.session_state.selected_staff_form
st.divider()

# ─── Load & filter ────────────────────────────────────────────────────────────
df = get_stock_df()
if "ผู้รับผิดชอบ" not in df.columns:
    df["ผู้รับผิดชอบ"] = ""

view = df[df["ผู้รับผิดชอบ"] == selected].copy() if selected != "ทั้งหมด" else df.copy()

if view.empty:
    st.warning(f"ยังไม่มีรายการที่ assign ให้ {selected}")
    st.stop()

# ─── Editable table ───────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">📦 รายการของ {selected} — {len(view)} รายการ</div>', unsafe_allow_html=True)
st.caption("แก้ไขตัวเลขในคอลัมน์ **คงเหลือ** ได้เลย แล้วกดบันทึกด้านล่าง")

edit_cols = ["ชื่อวัสดุ", "หน่วย", "คงเหลือ", "Reorder Point", "หมวดหมู่"]
edit_cols = [c for c in edit_cols if c in view.columns]

original = view[edit_cols].reset_index(drop=True)

edited = st.data_editor(
    original,
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in edit_cols if c != "คงเหลือ"],
    column_config={
        "คงเหลือ": st.column_config.NumberColumn("คงเหลือ", min_value=0, step=1)
    },
    height=420,
)

st.divider()

# ─── Save ─────────────────────────────────────────────────────────────────────
save_col, check_col = st.columns([1, 1], gap="large")

with save_col:
    if st.button("💾 บันทึกสต้อค", type="primary", use_container_width=True):
        try:
            staff_name = selected if selected != "ทั้งหมด" else "admin"
            count = save_stock_updates(edited, original, staff_name)
            if count:
                st.success(f"✓ บันทึก {count} รายการแล้ว")
            else:
                st.info("ไม่มีรายการที่เปลี่ยนแปลง")
        except Exception as e:
            st.error(f"บันทึกไม่สำเร็จ: {e}")

with check_col:
    if selected != "ทั้งหมด":
        if st.button(f"✓ บันทึกว่า {selected} เช็คสต้อคแล้ว", use_container_width=True):
            ok = record_stock_check(selected)
            if ok:
                st.success(f"บันทึกแล้ว — {date.today().strftime('%Y-%m-%d')}")
            else:
                st.error("บันทึกไม่สำเร็จ กรุณาลองใหม่ หรือเช็คการเชื่อมต่อ")
