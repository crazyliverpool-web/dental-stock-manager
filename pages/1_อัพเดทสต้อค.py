import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import date
from sheets import get_stock_df, save_stock_updates, record_stock_check
from utils import apply_styles, require_pin, require_user, get_current_user, pin_logout_button

st.set_page_config(page_title="อัพเดทสต้อค", page_icon="📋", layout="wide")
apply_styles()
pin_logout_button()

if not require_pin():
    st.stop()

if not require_user():
    st.stop()

current_user = get_current_user()

st.markdown('<div class="main-header">📋 อัพเดทสต้อค</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">ล็อกอินเป็น <b>{current_user}</b> — นับของแล้วใส่ตัวเลข กดบันทึกครั้งเดียว</div>', unsafe_allow_html=True)

# ─── Load & filter ────────────────────────────────────────────────────────────
df = get_stock_df()
if "ผู้รับผิดชอบ" not in df.columns:
    df["ผู้รับผิดชอบ"] = ""

view = df[df["ผู้รับผิดชอบ"] == current_user].copy()

if view.empty:
    st.warning(f"ยังไม่มีรายการที่ assign ให้ {current_user}")
    st.stop()

# ─── Editable table ───────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">📦 รายการของ {current_user} — {len(view)} รายการ</div>', unsafe_allow_html=True)
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
            count = save_stock_updates(edited, original, current_user)
            if count:
                st.success(f"✓ บันทึก {count} รายการแล้ว")
            else:
                st.info("ไม่มีรายการที่เปลี่ยนแปลง")
        except Exception as e:
            st.error(f"บันทึกไม่สำเร็จ: {e}")

with check_col:
    if st.button(f"✓ บันทึกว่า {current_user} เช็คสต้อคแล้ว", use_container_width=True):
        ok = record_stock_check(current_user)
        if ok:
            st.success(f"บันทึกแล้ว — {date.today().strftime('%Y-%m-%d')}")
        else:
            st.error("บันทึกไม่สำเร็จ กรุณาลองใหม่")
