import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import get_staff_list, add_staff, remove_staff, add_stock_item, get_stock_df
from utils import apply_styles, require_pin, require_user, pin_logout_button

st.set_page_config(page_title="จัดการข้อมูล", page_icon="⚙️", layout="wide")
apply_styles()
pin_logout_button()

if not require_pin():
    st.stop()

if not require_user():
    st.stop()

st.markdown('<div class="main-header">⚙️ จัดการข้อมูล</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">เพิ่มวัสดุ / จัดการพนักงาน</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📦 เพิ่มวัสดุ / อุปกรณ์", "👤 จัดการพนักงาน"])

# ─── Tab 1: เพิ่มวัสดุใหม่ ────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">เพิ่มรายการวัสดุหรืออุปกรณ์ใหม่</div>', unsafe_allow_html=True)

    staff_list = get_staff_list()

    existing_df = get_stock_df()
    existing_categories = sorted(existing_df["หมวดหมู่"].unique().tolist()) if "หมวดหมู่" in existing_df.columns else []

    with st.form("add_item_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("ชื่อวัสดุ / อุปกรณ์ *", placeholder="เช่น Composite Resin A2")
            unit = st.text_input("หน่วย *", placeholder="เช่น กล่อง, ขวด, ชิ้น")
            qty = st.number_input("จำนวนคงเหลือตั้งต้น", min_value=0, step=1, value=0)
        with c2:
            reorder = st.number_input("Reorder Point (สั่งเพิ่มเมื่อเหลือถึง)", min_value=0, step=1, value=5)
            category_input = st.selectbox(
                "หมวดหมู่",
                options=existing_categories + ["[ + เพิ่มหมวดหมู่ใหม่ ]"],
            )
            if category_input == "[ + เพิ่มหมวดหมู่ใหม่ ]":
                category = st.text_input("พิมพ์ชื่อหมวดหมู่ใหม่")
            else:
                category = category_input
            responsible = st.selectbox("ผู้รับผิดชอบ", options=[""] + staff_list)

        submitted = st.form_submit_button("➕ เพิ่มวัสดุ", type="primary", use_container_width=True)

        if submitted:
            if not item_name.strip():
                st.error("กรุณากรอกชื่อวัสดุ")
            elif not unit.strip():
                st.error("กรุณากรอกหน่วย")
            elif not category.strip():
                st.error("กรุณาเลือกหรือกรอกหมวดหมู่")
            else:
                ok = add_stock_item(item_name.strip(), unit.strip(), qty, reorder, category.strip(), responsible)
                if ok:
                    st.success(f"✓ เพิ่ม '{item_name.strip()}' เรียบร้อยแล้ว")
                    st.rerun()
                else:
                    st.error("เพิ่มไม่สำเร็จ — ตรวจสอบการเชื่อมต่อ Google Sheets")

# ─── Tab 2: จัดการพนักงาน ─────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">รายชื่อพนักงานปัจจุบัน</div>', unsafe_allow_html=True)

    staff_list = get_staff_list()

    if staff_list:
        for name in staff_list:
            col_name, col_btn = st.columns([4, 1])
            col_name.write(f"👤 {name}")
            if col_btn.button("ลบ", key=f"del_{name}", type="secondary"):
                ok = remove_staff(name)
                if ok:
                    st.success(f"ลบ '{name}' แล้ว")
                    st.rerun()
                else:
                    st.error("ลบไม่สำเร็จ")
    else:
        st.caption("ยังไม่มีรายชื่อพนักงาน")

    st.divider()
    st.markdown('<div class="section-title">เพิ่มพนักงานใหม่</div>', unsafe_allow_html=True)

    with st.form("add_staff_form", clear_on_submit=True):
        new_name = st.text_input("ชื่อพนักงาน *", placeholder="เช่น นุ่น")
        add_submitted = st.form_submit_button("➕ เพิ่มพนักงาน", type="primary", use_container_width=True)

        if add_submitted:
            if not new_name.strip():
                st.error("กรุณากรอกชื่อ")
            elif new_name.strip() in staff_list:
                st.warning(f"'{new_name.strip()}' มีอยู่แล้ว")
            else:
                ok = add_staff(new_name.strip())
                if ok:
                    st.success(f"✓ เพิ่ม '{new_name.strip()}' เรียบร้อยแล้ว")
                    st.rerun()
                else:
                    st.error("เพิ่มไม่สำเร็จ — ตรวจสอบการเชื่อมต่อ Google Sheets")

    st.info("💡 การเพิ่ม/ลบพนักงานจะมีผลทันทีกับทุกหน้าใน app")
