import os
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID          = os.getenv("SHEET_ID", "")
CREDENTIALS_PATH  = os.getenv("CREDENTIALS_PATH", "credentials/service_account.json")
LOCAL_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "history.json")


def _is_connected() -> bool:
    try:
        import streamlit as st
        return bool(st.secrets.get("SHEET_ID") or SHEET_ID)
    except Exception:
        return bool(SHEET_ID and os.path.exists(CREDENTIALS_PATH))


def _get_client():
    try:
        import streamlit as st
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    except Exception:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet_id() -> str:
    try:
        import streamlit as st
        return st.secrets.get("SHEET_ID", SHEET_ID)
    except Exception:
        return SHEET_ID


# ─── Stock ────────────────────────────────────────────────────────────────────

def get_stock_df() -> pd.DataFrame:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            return pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            print(f"[sheets] Stock read error: {e}")
    return _mock_stock()


def update_stock_qty(item_name: str, delta: int):
    """delta = +รับเข้า / -เบิกออก"""
    if _is_connected():
        try:
            sheet   = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                if row["ชื่อวัสดุ"] == item_name:
                    new_qty = max(0, int(row["คงเหลือ"]) + delta)
                    sheet.update_cell(i + 2, 3, new_qty)
                    return
        except Exception as e:
            print(f"[sheets] Stock update error: {e}")


def record_stock_check(staff_name: str):
    """บันทึกวันที่เช็คสต้อคของพนักงานคนนี้ในทุก row ที่รับผิดชอบ"""
    today = datetime.now().strftime("%Y-%m-%d")
    if _is_connected():
        try:
            sheet   = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            records = sheet.get_all_records()
            updates = []
            for i, row in enumerate(records):
                if row.get("ผู้รับผิดชอบ") == staff_name:
                    updates.append({"range": f"G{i+2}", "values": [[today]]})
            if updates:
                sheet.batch_update(updates)
            return True
        except Exception as e:
            print(f"[sheets] Check date error: {e}")
    return True


def get_staff_list() -> list:
    """อ่านรายชื่อพนักงานจาก Staff sheet — fallback เป็น hardcode ถ้า sheet ยังไม่มี"""
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Staff")
            records = sheet.get_all_records()
            names = [r["ชื่อ"] for r in records if r.get("ชื่อ")]
            if names:
                return names
        except Exception as e:
            print(f"[sheets] Staff read error: {e}")
    return ["เปิ้ล", "ซะห์", "อาร์ม", "มี", "ฉ้ะ", "ฟีร่า", "ฮัน", "กะละห์"]


def add_staff(name: str) -> bool:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Staff")
            sheet.append_row([name])
            return True
        except Exception as e:
            print(f"[sheets] Add staff error: {e}")
    return False


def remove_staff(name: str) -> bool:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Staff")
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                if row.get("ชื่อ") == name:
                    sheet.delete_rows(i + 2)
                    return True
        except Exception as e:
            print(f"[sheets] Remove staff error: {e}")
    return False


def add_stock_item(name: str, unit: str, qty: int, reorder: int, category: str, responsible: str) -> bool:
    """เพิ่มรายการวัสดุใหม่ลง Stock sheet"""
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            sheet.append_row([name, unit, qty, reorder, category, responsible, ""])
            return True
        except Exception as e:
            print(f"[sheets] Add item error: {e}")
    return False


def get_staff_check_summary(df: pd.DataFrame) -> dict:
    """คืน dict {staff_name: last_check_date or None} สำหรับทุก staff"""
    if "ผู้รับผิดชอบ" not in df.columns or "วันที่เช็คล่าสุด" not in df.columns:
        return {}
    result = {}
    for staff, group in df.groupby("ผู้รับผิดชอบ"):
        if not staff:
            continue
        dates = group["วันที่เช็คล่าสุด"].replace("", pd.NA).dropna()
        result[staff] = dates.max() if not dates.empty else None
    return result


# ─── History ──────────────────────────────────────────────────────────────────

def add_history(transaction_type: str, item_name: str, qty: int, note: str, user: str):
    entry = {
        "วันที่":        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ประเภท":       transaction_type,
        "ชื่อวัสดุ":    item_name,
        "จำนวน":        qty,
        "หมายเหตุ":     note,
        "ผู้ทำรายการ":  user,
    }
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("History")
            sheet.append_row(list(entry.values()))
            return
        except Exception as e:
            print(f"[sheets] History write error: {e}")
    _local_append(entry)


def get_history_df() -> pd.DataFrame:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("History")
            data  = sheet.get_all_records()
            if data:
                return pd.DataFrame(data)
        except Exception as e:
            print(f"[sheets] History read error: {e}")
    return _local_read()


# ─── Pending Sync (DirectEditLog) ────────────────────────────────────────────

def get_pending_syncs() -> pd.DataFrame:
    """อ่าน DirectEditLog เฉพาะ row ที่ยังไม่ได้ confirm (สถานะว่าง)"""
    if not _is_connected():
        return pd.DataFrame()
    try:
        sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("DirectEditLog")
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        if "สถานะ" not in df.columns:
            df["สถานะ"] = ""
        df["_row"] = range(2, len(df) + 2)
        return df[df["สถานะ"].astype(str).str.strip() == ""].reset_index(drop=True)
    except Exception as e:
        print(f"[sheets] DirectEditLog read error: {e}")
        return pd.DataFrame()


def confirm_sync(sheet_row: int, item_name: str, col_name: str,
                 old_val: str, new_val: str, staff: str, timestamp: str) -> bool:
    """เขียน History + mark DirectEditLog row ว่าเสร็จแล้ว"""
    if not _is_connected():
        return False
    try:
        ss = _get_client().open_by_key(_get_sheet_id())

        qty  = int(new_val) if col_name == "คงเหลือ" and str(new_val).lstrip("-").isdigit() else 0
        note = f"{col_name}: {old_val} → {new_val} (sync จาก Sheet)"
        ss.worksheet("History").append_row(
            [timestamp, "อัพเดทสต้อค", item_name, qty, note, staff]
        )

        log     = ss.worksheet("DirectEditLog")
        headers = log.row_values(1)
        if "สถานะ" not in headers:
            log.update_cell(1, len(headers) + 1, "สถานะ")
            status_col = len(headers) + 1
        else:
            status_col = headers.index("สถานะ") + 1

        confirmed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        log.update_cell(sheet_row, status_col, f"✅ {staff} ({confirmed_at})")
        return True
    except Exception as e:
        print(f"[sheets] confirm_sync error: {e}")
        return False


# ─── Local JSON fallback ──────────────────────────────────────────────────────

def _local_append(entry: dict):
    records = _local_load()
    records.append(entry)
    with open(LOCAL_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _local_read() -> pd.DataFrame:
    records = _local_load()
    if records:
        return pd.DataFrame(records)
    return _mock_history()


def _local_load() -> list:
    if os.path.exists(LOCAL_HISTORY_FILE):
        with open(LOCAL_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ─── Mock Data ────────────────────────────────────────────────────────────────

def _mock_stock() -> pd.DataFrame:
    return pd.DataFrame([
        {"ชื่อวัสดุ": "Composite Resin (Filtek Z350)",      "หน่วย": "กล่อง",    "คงเหลือ": 3,  "Reorder Point": 5,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Bonding Agent (Adper Single Bond)",  "หน่วย": "ขวด",      "คงเหลือ": 2,  "Reorder Point": 3,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Glass Ionomer Cement (Fuji IX)",     "หน่วย": "กระป๋อง",  "คงเหลือ": 8,  "Reorder Point": 4,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Impression Material (Aquasil)",      "หน่วย": "กล่อง",    "คงเหลือ": 1,  "Reorder Point": 3,  "หมวดหมู่": "Impression"},
        {"ชื่อวัสดุ": "Lidocaine 2% (ยาชา)",                "หน่วย": "กล่อง",    "คงเหลือ": 12, "Reorder Point": 10, "หมวดหมู่": "Anesthetic"},
        {"ชื่อวัสดุ": "Gloves Size M",                      "หน่วย": "กล่อง",    "คงเหลือ": 4,  "Reorder Point": 5,  "หมวดหมู่": "PPE"},
        {"ชื่อวัสดุ": "Face Mask",                          "หน่วย": "กล่อง",    "คงเหลือ": 6,  "Reorder Point": 5,  "หมวดหมู่": "PPE"},
        {"ชื่อวัสดุ": "Etchant Gel 37%",                    "หน่วย": "หลอด",     "คงเหลือ": 7,  "Reorder Point": 4,  "หมวดหมู่": "Restorative"},
    ])


def _mock_history() -> pd.DataFrame:
    return pd.DataFrame([
        {"วันที่": "2026-05-10 09:15", "ประเภท": "รับเข้า", "ชื่อวัสดุ": "Gloves Size M",                     "จำนวน": 5, "หมายเหตุ": "สั่งซื้อรายเดือน", "ผู้ทำรายการ": "นุ่น"},
        {"วันที่": "2026-05-11 10:30", "ประเภท": "เบิกออก", "ชื่อวัสดุ": "Composite Resin (Filtek Z350)",    "จำนวน": 2, "หมายเหตุ": "ห้องตรวจ 1",       "ผู้ทำรายการ": "ปุ้ม"},
        {"วันที่": "2026-05-12 08:45", "ประเภท": "เบิกออก", "ชื่อวัสดุ": "Lidocaine 2% (ยาชา)",             "จำนวน": 1, "หมายเหตุ": "ห้องตรวจ 2",       "ผู้ทำรายการ": "นุ่น"},
        {"วันที่": "2026-05-12 14:00", "ประเภท": "รับเข้า", "ชื่อวัสดุ": "Bonding Agent (Adper Single Bond)","จำนวน": 3, "หมายเหตุ": "สั่งซื้อเพิ่ม",    "ผู้ทำรายการ": "ปุ้ม"},
        {"วันที่": "2026-05-13 09:00", "ประเภท": "เบิกออก", "ชื่อวัสดุ": "Face Mask",                        "จำนวน": 1, "หมายเหตุ": "ใช้ประจำวัน",     "ผู้ทำรายการ": "นุ่น"},
    ])
