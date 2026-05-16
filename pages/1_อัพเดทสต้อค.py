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

# ─── Load data ────────────────────────────────────────────────────────────────
df = get_stock_df()
if "ผู้รับผิดชอบ" not in df.columns:
    df["ผู้รับผิดชอบ"] = ""

all_items = df[df["ผู้รับผิดชอบ"] == current_user].copy()

if all_items.empty:
    st.warning(f"ยังไม่มีรายการที่ assign ให้ {current_user}")
    st.stop()

# ─── Search & Filter ──────────────────────────────────────────────────────────
f_col1, f_col2, f_col3 = st.columns([3, 2, 2])

with f_col1:
    search = st.text_input("🔍 ค้นหาชื่อวัสดุ", placeholder="พิมพ์ชื่อ...", label_visibility="collapsed")

with f_col2:
    categories = ["ทุกหมวด"] + sorted(all_items["หมวดหมู่"].unique().tolist()) if "หมวดหมู่" in all_items.columns else ["ทุกหมวด"]
    cat_filter = st.selectbox("หมวดหมู่", categories, label_visibility="collapsed")

with f_col3:
    low_only = st.checkbox("⚠️ เฉพาะที่ต้องสั่งเพิ่ม")

# ─── Apply filters ────────────────────────────────────────────────────────────
view = all_items.copy()

if search:
    mask = view["ชื่อวัสดุ"].str.contains(search, case=False, na=False)
    for col in ["ชื่อสามัญ", "ชื่อทางการค้า"]:
        if col in view.columns:
            mask = mask | view[col].str.contains(search, case=False, na=False)
    view = view[mask]

if cat_filter != "ทุกหมวด":
    view = view[view["หมวดหมู่"] == cat_filter]

if low_only and "Reorder Point" in view.columns:
    view = view[view["คงเหลือ"] <= view["Reorder Point"]]

# ─── Editable table ───────────────────────────────────────────────────────────
total = len(all_items)
showing = len(view)
label = f"📦 {current_user} — แสดง {showing}/{total} รายการ"
st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)
st.caption("แก้ไขตัวเลขในคอลัมน์ **คงเหลือ** ได้เลย แล้วกดบันทึกด้านล่าง")

edit_cols = ["ชื่อวัสดุ", "ชื่อสามัญ", "ชื่อทางการค้า", "หน่วย", "คงเหลือ", "Reorder Point", "หมวดหมู่"]
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
