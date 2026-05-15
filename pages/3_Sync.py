import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import get_pending_syncs, confirm_sync, get_staff_list

STAFF = get_staff_list()

st.set_page_config(page_title="Pending Sync", page_icon="🔄", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #4FC3F7; margin-bottom: 0.25rem; }
    .sub-header  { font-size: 0.9rem; color: #888; margin-bottom: 1.5rem; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #4FC3F7;
        border-bottom: 1px solid #2A3040; padding-bottom: 0.4rem; margin-bottom: 1rem;
    }
    .sync-card {
        background: #1A1F2E; border: 1px solid #2A3040;
        border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
    }
    .sync-item  { font-size: 1rem; font-weight: 600; color: #E0E0E0; }
    .sync-diff  { font-size: 0.9rem; color: #888; margin-top: 0.25rem; }
    .sync-arrow { color: #4FC3F7; font-weight: 700; }
    .sync-time  { font-size: 0.8rem; color: #555; margin-top: 0.2rem; }
    hr { border-color: #2A3040 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🔄 Pending Sync</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">รายการที่แก้ใน Sheet โดยตรง — รอ confirm เพื่อบันทึกลง History</div>',
            unsafe_allow_html=True)

# ─── Load pending ─────────────────────────────────────────────────────────────
pending = get_pending_syncs()

if pending.empty:
    st.success("✅ ไม่มีรายการที่รอ sync — ทุกอย่าง up-to-date แล้ว")
    st.stop()

# ─── Header summary ───────────────────────────────────────────────────────────
st.warning(f"พบ **{len(pending)} รายการ** ที่แก้ใน Sheet โดยตรง รอ confirm เพื่อบันทึกลง History")

st.divider()

# ─── Confirm all ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">✅ Confirm ทั้งหมดพร้อมกัน</div>', unsafe_allow_html=True)

col_staff, col_btn = st.columns([2, 1], gap="large")
with col_staff:
    global_staff = st.selectbox(
        "ระบุพนักงานที่แก้ข้อมูล",
        ["— เลือก —"] + STAFF,
        key="global_staff"
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    confirm_all = st.button(
        f"✅ Confirm {len(pending)} รายการ",
        type="primary",
        use_container_width=True,
        disabled=(global_staff == "— เลือก —"),
    )

if confirm_all:
    success, fail = 0, 0
    for _, row in pending.iterrows():
        ok = confirm_sync(
            int(row["_row"]), str(row.get("รายการ", "")),
            str(row.get("คอลัมน์", "")), str(row.get("ค่าเดิม", "")),
            str(row.get("ค่าใหม่", "")), global_staff, str(row.get("เวลา", ""))
        )
        if ok: success += 1
        else:  fail   += 1

    if success:
        st.success(f"✅ Confirm {success} รายการ — บันทึกลง History แล้ว")
    if fail:
        st.error(f"❌ {fail} รายการล้มเหลว กรุณาลองใหม่")
    st.rerun()

st.divider()

# ─── Individual confirm ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">หรือ Confirm ทีละรายการ</div>', unsafe_allow_html=True)

for idx, row in pending.iterrows():
    with st.container():
        st.markdown(f"""
        <div class="sync-card">
            <div class="sync-item">📦 {row.get("รายการ", "")}</div>
            <div class="sync-diff">
                {row.get("คอลัมน์", "")} &nbsp;
                <span style="color:#888">{row.get("ค่าเดิม", "")}</span>
                &nbsp;<span class="sync-arrow">→</span>&nbsp;
                <span style="color:#4FC3F7; font-weight:600">{row.get("ค่าใหม่", "")}</span>
            </div>
            <div class="sync-time">🕐 {row.get("เวลา", "")}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1], gap="small")
        with c1:
            staff_sel = st.selectbox(
                "พนักงาน",
                ["— เลือก —"] + STAFF,
                key=f"staff_{idx}",
                label_visibility="collapsed"
            )
        with c2:
            if st.button("✅ Confirm", key=f"confirm_{idx}",
                         disabled=(staff_sel == "— เลือก —"),
                         use_container_width=True):
                ok = confirm_sync(
                    int(row["_row"]), str(row.get("รายการ", "")),
                    str(row.get("คอลัมน์", "")), str(row.get("ค่าเดิม", "")),
                    str(row.get("ค่าใหม่", "")), staff_sel, str(row.get("เวลา", ""))
                )
                if ok:
                    st.success(f"✅ บันทึกแล้ว")
                    st.rerun()
                else:
                    st.error("บันทึกไม่สำเร็จ")
