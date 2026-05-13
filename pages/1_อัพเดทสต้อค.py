import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from sheets import get_stock_df, record_stock_check

load_dotenv()

STAFF = ["เปิ้ล", "ซะห์", "อาร์ม", "มี", "ฉ้ะ", "ฟีร่า", "ฮัน", "กะละห์"]

st.set_page_config(page_title="อัพเดทสต้อค", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #4FC3F7; margin-bottom: 0.25rem; }
    .sub-header  { font-size: 0.9rem; color: #888; margin-bottom: 1.5rem; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #4FC3F7;
        border-bottom: 1px solid #2A3040; padding-bottom: 0.4rem; margin-bottom: 1rem;
    }
    .staff-label { font-size: 0.85rem; color: #888; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

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

edited = st.data_editor(
    view[edit_cols].reset_index(drop=True),
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
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
            creds  = Credentials.from_service_account_file(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials", "service_account.json"),
                scopes=SCOPES
            )
            sheet   = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID","")).worksheet("Stock")
            records = sheet.get_all_records()
            updates = []
            for _, erow in edited.iterrows():
                for j, srow in enumerate(records):
                    if srow["ชื่อวัสดุ"] == erow["ชื่อวัสดุ"]:
                        updates.append({"range": f"C{j+2}", "values": [[int(erow["คงเหลือ"])]]})
                        break
            if updates:
                sheet.batch_update(updates)
            st.success(f"✓ บันทึก {len(updates)} รายการแล้ว")
        except Exception as e:
            st.error(f"บันทึกไม่สำเร็จ: {e}")

with check_col:
    if selected != "ทั้งหมด":
        if st.button(f"✓ บันทึกว่า {selected} เช็คสต้อคแล้ว", use_container_width=True):
            record_stock_check(selected)
            st.success(f"บันทึกแล้ว — {date.today().strftime('%Y-%m-%d')}")
