import streamlit as st
import pandas as pd
from datetime import datetime, date
from sheets import get_stock_df, get_staff_check_summary

st.set_page_config(page_title="Dental Stock Manager", page_icon="🦷", layout="wide")

STAFF = ["ทั้งหมด", "เปิ้ล", "ซะห์", "อาร์ม", "มี", "ฉ้ะ", "ฟีร่า", "ฮัน", "กะละห์"]

st.markdown("""
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🦷 Dental Stock Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ระบบจัดการสต้อควัสดุทันตกรรม</div>', unsafe_allow_html=True)

# ─── Staff selector ───────────────────────────────────────────────────────────
st.markdown('<div class="staff-label">👤 เลือกพนักงาน</div>', unsafe_allow_html=True)

if "selected_staff" not in st.session_state:
    st.session_state.selected_staff = "ทั้งหมด"

cols = st.columns(len(STAFF))
for i, name in enumerate(STAFF):
    btn_type = "primary" if st.session_state.selected_staff == name else "secondary"
    if cols[i].button(name, key=f"staff_{name}", type=btn_type, use_container_width=True):
        st.session_state.selected_staff = name
        st.rerun()

selected = st.session_state.selected_staff
st.divider()

# ─── Stock check status ───────────────────────────────────────────────────────
df_all = get_stock_df()
check_summary = get_staff_check_summary(df_all)
today         = date.today()
this_month    = today.strftime("%Y-%m")

st.markdown('<div class="section-title">📅 สถานะเช็คสต้อคประจำเดือน</div>', unsafe_allow_html=True)

check_cols = st.columns(len(STAFF) - 1)  # ไม่นับ "ทั้งหมด"
for i, name in enumerate(STAFF[1:]):
    last = check_summary.get(name)
    checked_this_month = last and str(last).startswith(this_month)

    if checked_this_month:
        css, icon, label = "check-ok",   "✓", f"เช็คแล้ว\n{last}"
    elif today.day >= 28:
        css, icon, label = "check-late", "🚨", "เลยกำหนด!"
    elif today.day >= 20:
        css, icon, label = "check-warn", "⚠️", "ยังไม่เช็ค"
    else:
        css, icon, label = "check-none", "–", last if last else "ยังไม่มีข้อมูล"

    check_cols[i].markdown(
        f'<div class="{css}"><b>{name}</b><br>{icon} {label}</div>',
        unsafe_allow_html=True
    )

st.divider()

# ─── Load & filter data ───────────────────────────────────────────────────────
df = df_all

if "ผู้รับผิดชอบ" not in df.columns:
    df["ผู้รับผิดชอบ"] = ""

if selected != "ทั้งหมด":
    view = df[df["ผู้รับผิดชอบ"] == selected].copy()
    st.markdown(f'<div class="section-title">📋 ของที่ {selected} รับผิดชอบ</div>', unsafe_allow_html=True)
else:
    view = df.copy()
    st.markdown('<div class="section-title">📋 สต้อควัสดุทั้งหมด</div>', unsafe_allow_html=True)

low_stock = view[view["คงเหลือ"] <= view["Reorder Point"]]

# ─── Metrics ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("รายการทั้งหมด", len(view))
col2.metric("สต้อคปกติ", len(view) - len(low_stock))
col3.metric("ต้องสั่งเพิ่ม", len(low_stock),
            delta=f"-{len(low_stock)}" if len(low_stock) > 0 else None,
            delta_color="inverse")

# ─── Low stock alert ──────────────────────────────────────────────────────────
if not low_stock.empty:
    items_html = "".join(
        f'<div class="alert-item">• {row["ชื่อวัสดุ"]} — เหลือ {row["คงเหลือ"]} {row["หน่วย"]} (Reorder: {row["Reorder Point"]})</div>'
        for _, row in low_stock.iterrows()
    )
    st.markdown(f"""
    <div class="alert-box">
        <div class="alert-title">⚠️ วัสดุที่ต้องสั่งเพิ่ม ({len(low_stock)} รายการ)</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

# ─── Stock table ──────────────────────────────────────────────────────────────
def highlight_low(row):
    if row["คงเหลือ"] <= row["Reorder Point"]:
        return ["color: #E57373"] * len(row)
    return ["color: #A5D6A7"] * len(row)

display_cols = ["ชื่อวัสดุ", "หน่วย", "คงเหลือ", "Reorder Point", "หมวดหมู่", "ผู้รับผิดชอบ"]
display_cols = [c for c in display_cols if c in view.columns]

st.dataframe(
    view[display_cols].style.apply(highlight_low, axis=1),
    use_container_width=True, hide_index=True, height=360,
)

st.divider()

# ─── Chart ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 สต้อคตามหมวดหมู่</div>', unsafe_allow_html=True)
categories = ["ทั้งหมด"] + sorted(view["หมวดหมู่"].unique().tolist())
selected_cat = st.selectbox("เลือกหมวดหมู่", categories, label_visibility="collapsed")
filtered = view if selected_cat == "ทั้งหมด" else view[view["หมวดหมู่"] == selected_cat]
st.bar_chart(filtered.set_index("ชื่อวัสดุ")["คงเหลือ"], use_container_width=True, height=280)
