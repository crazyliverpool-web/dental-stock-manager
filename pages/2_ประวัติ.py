import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import get_history_df

st.set_page_config(page_title="ประวัติการทำรายการ", page_icon="🗂️", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #4FC3F7; margin-bottom: 0.25rem; }
    .sub-header  { font-size: 0.9rem; color: #888; margin-bottom: 1.5rem; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #4FC3F7;
        border-bottom: 1px solid #2A3040; padding-bottom: 0.4rem; margin-bottom: 1rem;
    }
    .badge-in  { color: #66BB6A; font-weight: 600; }
    .badge-out { color: #E57373; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🗂️ ประวัติการทำรายการ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Log การรับเข้าและเบิกออกทั้งหมด</div>', unsafe_allow_html=True)

df = get_history_df()

# ─── Summary metrics ──────────────────────────────────────────────────────────
total_in  = len(df[df["ประเภท"] == "รับเข้า"])
total_out = len(df[df["ประเภท"] == "เบิกออก"])

col1, col2, col3 = st.columns(3)
col1.metric("รายการทั้งหมด", len(df))
col2.metric("รับเข้า", total_in)
col3.metric("เบิกออก", total_out)

st.divider()

# ─── Filters ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔍 ค้นหา / กรอง</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)

with f1:
    filter_type = st.selectbox("ประเภท", ["ทั้งหมด", "รับเข้า", "เบิกออก"])
with f2:
    items = ["ทั้งหมด"] + sorted(df["ชื่อวัสดุ"].unique().tolist())
    filter_item = st.selectbox("ชื่อวัสดุ", items)
with f3:
    users = ["ทั้งหมด"] + sorted(df["ผู้ทำรายการ"].unique().tolist())
    filter_user = st.selectbox("ผู้ทำรายการ", users)

filtered = df.copy()
if filter_type != "ทั้งหมด":
    filtered = filtered[filtered["ประเภท"] == filter_type]
if filter_item != "ทั้งหมด":
    filtered = filtered[filtered["ชื่อวัสดุ"] == filter_item]
if filter_user != "ทั้งหมด":
    filtered = filtered[filtered["ผู้ทำรายการ"] == filter_user]

st.divider()

# ─── History table ────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">📋 รายการ ({len(filtered)} รายการ)</div>', unsafe_allow_html=True)

def highlight_type(row):
    if row["ประเภท"] == "รับเข้า":
        return ["color: #66BB6A"] * len(row)
    return ["color: #E57373"] * len(row)

st.dataframe(
    filtered.sort_values("วันที่", ascending=False).style.apply(highlight_type, axis=1),
    use_container_width=True,
    hide_index=True,
    height=420,
)

# ─── Usage chart ──────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">📊 วัสดุที่เบิกมากที่สุด</div>', unsafe_allow_html=True)

out_df = df[df["ประเภท"] == "เบิกออก"].groupby("ชื่อวัสดุ")["จำนวน"].sum().sort_values(ascending=False)
if not out_df.empty:
    st.bar_chart(out_df, use_container_width=True, height=260)
else:
    st.caption("ยังไม่มีข้อมูลการเบิก")
