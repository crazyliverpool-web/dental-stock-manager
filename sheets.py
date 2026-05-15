import os
import re
import json
import difflib
import pandas as pd
import gspread
import streamlit as st
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


def _get_client():
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    except Exception:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet_id() -> str:
    try:
        return st.secrets.get("SHEET_ID", SHEET_ID)
    except Exception:
        return SHEET_ID


def _is_connected() -> bool:
    try:
        sid       = st.secrets.get("SHEET_ID", "") or SHEET_ID
        has_creds = "gcp_service_account" in st.secrets or os.path.exists(CREDENTIALS_PATH)
        return bool(sid and has_creds)
    except Exception:
        return bool(SHEET_ID and os.path.exists(CREDENTIALS_PATH))


def _find_col(headers: list, col_name: str) -> int:
    """Return 1-based column index; raises ValueError if not found."""
    try:
        return headers.index(col_name) + 1
    except ValueError:
        raise ValueError(f"Column '{col_name}' not found in sheet headers: {headers}")


def _a1_col(col: int) -> str:
    """Convert 1-based column number to A1-notation letter(s), e.g. 3 → 'C'."""
    return gspread.utils.rowcol_to_a1(1, col).rstrip("0123456789")


# ─── Stock ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_stock_df() -> pd.DataFrame:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            return pd.DataFrame(sheet.get_all_records())
        except Exception as e:
            print(f"[sheets] Stock read error: {e}")
    return _mock_stock()


def save_stock_updates(edited_df: pd.DataFrame, original_df: pd.DataFrame, staff_name: str) -> int:
    """
    Batch-update changed คงเหลือ values in Stock sheet and log one history
    entry per changed item. Returns the number of rows actually updated.
    """
    if not _is_connected():
        return 0

    changed_mask = edited_df["คงเหลือ"].values != original_df["คงเหลือ"].values
    if not changed_mask.any():
        return 0

    sheet        = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
    headers      = sheet.row_values(1)
    col_qty      = _find_col(headers, "คงเหลือ")
    col_ltr      = _a1_col(col_qty)
    records      = sheet.get_all_records()
    name_to_row  = {r["ชื่อวัสดุ"]: i + 2 for i, r in enumerate(records)}

    updates, history = [], []
    for idx in edited_df.index[changed_mask]:
        item_name = edited_df.at[idx, "ชื่อวัสดุ"]
        new_qty   = int(edited_df.at[idx, "คงเหลือ"])
        old_qty   = int(original_df.at[idx, "คงเหลือ"])
        row_num   = name_to_row.get(item_name)
        if row_num:
            updates.append({"range": f"{col_ltr}{row_num}", "values": [[new_qty]]})
            history.append((item_name, old_qty, new_qty))

    if updates:
        sheet.batch_update(updates)

    for item_name, old_qty, new_qty in history:
        add_history("อัพเดทสต้อค", item_name, new_qty,
                    f"{old_qty} → {new_qty}", staff_name)

    get_stock_df.clear()
    return len(updates)


def record_stock_check(staff_name: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    if _is_connected():
        try:
            sheet    = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            headers  = sheet.row_values(1)
            col_date = _find_col(headers, "วันที่เช็คล่าสุด")
            col_ltr  = _a1_col(col_date)
            records  = sheet.get_all_records()
            updates  = [
                {"range": f"{col_ltr}{i+2}", "values": [[today]]}
                for i, row in enumerate(records)
                if row.get("ผู้รับผิดชอบ") == staff_name
            ]
            if updates:
                sheet.batch_update(updates)
            get_stock_df.clear()
            return True
        except Exception as e:
            print(f"[sheets] Check date error: {e}")
    return True


def get_staff_list() -> list:
    if _is_connected():
        try:
            sheet   = _get_client().open_by_key(_get_sheet_id()).worksheet("Staff")
            records = sheet.get_all_records()
            names   = [r["ชื่อ"] for r in records if r.get("ชื่อ")]
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
            sheet   = _get_client().open_by_key(_get_sheet_id()).worksheet("Staff")
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                if row.get("ชื่อ") == name:
                    sheet.delete_rows(i + 2)
                    return True
        except Exception as e:
            print(f"[sheets] Remove staff error: {e}")
    return False


def add_stock_item(name: str, unit: str, qty: int, reorder: int, category: str, responsible: str) -> bool:
    if _is_connected():
        try:
            sheet = _get_client().open_by_key(_get_sheet_id()).worksheet("Stock")
            sheet.append_row([name, unit, qty, reorder, category, responsible, ""])
            get_stock_df.clear()
            return True
        except Exception as e:
            print(f"[sheets] Add item error: {e}")
    return False


def get_staff_check_summary(df: pd.DataFrame) -> dict:
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


# ─── Sync from monthly check sheet ───────────────────────────────────────────

CHECK_SHEET_ID = "1TTjDAnrsRaUh-YHRzs3FHWKKhO8BExO5hYk-iwdSE9Y"

_SHEET_STAFF = {
    "อินอาร์ม": "อาร์ม",
    "พี่เปิ้ล":  "เปิ้ล",
    "ฮัน":       "ฮัน",
    "ฟีร่า":     "ฟีร่า",
    "กะมี":      "มี",
    "อิสสะห์":  "ซะห์",
    "ดารณี":     "ฉ้ะ",
}
_QTY_COL_B = {"ฮัน", "อิสสะห์"}

_ALIAS = {
    "บอนดิ้ง oppibal universal solo":    "บอนดิ้ง optibal universal solo",
    "บอนดิ้ิ้ง (ติดเครื่องมือ 3m)":      "บอนดิ้งติดเครื่องมือ 3m",
    "เอชชิ่ง fine ecth37 หลอดเขียว":     "เอชชิ่ง fine etch37 หลอดเขียว",
    "ultra-etch (เอชชิ้งหลอดสีฟ้า)":    "ultra-etch เอชชิ้งหลอดสีฟ้า",
    "เอชชิ้งกรด(ครอบฟัน)":              "เอชชิ้งกรด (ครอบฟัน)",
    "gren gloo (กาวหลอดสีเขียว)":        "gren gloo กาวหลอดสีเขียว",
    "tarnsbond ( กาว3mติดเครื่องมือ )":  "transbond กาว 3m ติดเครื่องมือ",
    "flowธรรมดา":                        "flow ธรรมดา",
    "บล้อกเหงือกฟอกสีฟัน":              "บล็อกเหงือกฟอกสีฟัน",
    "n flow a3.5d":                      "n flow a3.5",
    "flowable  filtek (3m )     a3":     "flowable filtek 3m a3",
    "hamonize a1e": "harmonize a1e", "hamonize a2e": "harmonize a2e",
    "hamonize a1d": "harmonize a1d", "hamonize a2d": "harmonize a2d",
    "hamonize a3d": "harmonize a3d",
    "filtek (z350) a1": "filtek z350 a1", "filtek (z350) a2": "filtek z350 a2",
    "filtek (z350) a3": "filtek z350 a3", "filtek (z350) a3.5": "filtek z350 a3.5",
    "filtek (z350) a4": "filtek z350 a4", "filtek (z250) a3": "filtek z250 a3",
    "filtek (z250) a3.5": "filtek z250 a3.5",
    "g-aenial universal (หลอดสีน้ำตาล) a2": "g-aenial universal a2",
    "g-aenial universal (หลอดสีน้ำตาล) a3": "g-aenial universal a3",
    "topicalยาชาสตอเบอร์รี่": "topical ยาชาสตอเบอร์รี่",
    "ยาพาราแคพ500mg": "ยาพาราแคพ", "ยาพาราเซตามอล 500mg": "ยาพาราแคพ",
    "ยาอม็อกซี่ 500mg": "ยาอม็อกซี่", "ไอบูโพรเฟน 400mg": "ไอบูโพรเฟน",
    "ซาร่าน้ำ เด็ก 120mg": "ซาร่าน้ำ เด็ก",
    "3.5 fox": "retainer 3.5 fox", "3.5 monkey": "retainer 3.5 monkey",
    "3.5 penguin": "retainer 3.5 penguin", "6.5 fox": "retainer 6.5 fox",
    "5.0 fox": "retainer 5.0 fox", "3.5 rabbit": "retainer 3.5 rabbit",
    "bkt dtc ไม่มีฮุก": "bkt dtc ไม่มีฮุค", "bkt dtc มีฮุก": "bkt dtc มีฮุค",
    "bkt เกาหลี มีฮุก345": "bkt เกาหลี มีฮุค 345", "bkt ao022": "bkt ao 022",
    "mbt 018ใหม่": "mbt 018 ใหม่",
    "ทิชชู่สเตอร์ไรด์": "ทิชชู่สเตอร์ไรล์", "ทิชชู่ใช้ในห้องน้ำ": "ทิชชู่ห้องน้ำ",
    "พู่กันขาว (s)": "พู่กันขาว s", "พู่กันเหลือง (m)": "พู่กันเหลือง m",
    "พู่กันเขียว (l)": "พู่กันเขียว l",
    "โซเดียมไฮเปอร์คลอไลท์ (เขียว) 2.5%": "โซเดียมไฮเปอร์คลอไรท์ 2.5% เขียว",
    "alcohol ขวดเล็ก/ขวดใหญ่": "alcohol", "maks": "mask",
    "12 niti บน ": "ลวด 12 niti บน", "12 niti ล่าง": "ลวด 12 niti ล่าง",
    "14 niti บน ": "ลวด 14 niti บน", "14 niti ล่าง": "ลวด 14 niti ล่าง",
    "16 niti บน ": "ลวด 16 niti บน", "16 niti ล่าง": "ลวด 16 niti ล่าง",
    "18 niti บน ": "ลวด 18 niti บน", "18 niti ล่าง": "ลวด 18 niti ล่าง",
    "16x22 niti บน": "ลวด 16x22 niti บน", "16x22 niti ล่าง": "ลวด 16x22 niti ล่าง",
    "17x25 niti บน": "ลวด 17x25 niti บน", "17x25 niti ล่าง": "ลวด 17x25 niti ล่าง",
    "19x25 niti บน": "ลวด 19x25 niti บน", "19x25 niti ล่าง": "ลวด 19x25 niti ล่าง",
    "18 ss บน": "ลวด 18 ss บน", "18 ssล่าง": "ลวด 18 ss ล่าง",
    "16*22 ss บน": "ลวด 16x22 ss บน", "16x22 ss ล่าง": "ลวด 16x22 ss ล่าง",
    "17*25 ss บน": "ลวด 17x25 ss บน", "19*25 ss บน": "ลวด 19x25 ss บน",
    "16*16 ss บน": "ลวด 16x16 ss บน",
    "12seบน": "ลวด 12 se บน", "12seล่าง": "ลวด 12 se ล่าง",
    "14seบน": "ลวด 14 se บน", "14seล่าง": "ลวด 14 se ล่าง",
    "16seบน": "ลวด 16 se บน", "16seล่าง": "ลวด 16 se ล่าง",
    "18seบน": "ลวด 18 se บน", "18seล่าง": "ลวด 18 se ล่าง",
    "19*25seบน": "ลวด 19x25 se บน", "19*25seล่าง": "ลวด 19x25 se ล่าง",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _parse_qty(s: str):
    m = re.search(r"\d+", str(s))
    return int(m.group()) if m else None


def _read_check_ws(ws) -> list:
    rows = ws.get_all_values()
    qty_col = 1 if ws.title in _QTY_COL_B else 2
    items = []
    for row in rows[1:]:
        if len(row) <= qty_col:
            continue
        name = row[0].strip()
        if not name:
            continue
        qty = _parse_qty(row[qty_col])
        if qty is not None:
            items.append((name, qty))
    return items


def sync_from_check_sheet() -> dict:
    """ดึงข้อมูลจาก sheet เช็คสต๊อกรายเดือน แล้วอัพเดทลง Stock
    Returns: {"matched": int, "updated": int, "skipped": int, "details": list}
    """
    gc  = _get_client()
    src = gc.open_by_key(CHECK_SHEET_ID)
    dst = gc.open_by_key(_get_sheet_id()).worksheet("Stock")

    records  = dst.get_all_records()
    headers  = dst.row_values(1)
    col_qty  = headers.index("คงเหลือ") + 1
    col_date = headers.index("วันที่เช็คล่าสุด") + 1
    col_ltr      = gspread.utils.rowcol_to_a1(1, col_qty).rstrip("0123456789")
    col_date_ltr = gspread.utils.rowcol_to_a1(1, col_date).rstrip("0123456789")

    stock_index = {_norm(r["ชื่อวัสดุ"]): {"row": i+2, "cur_qty": r["คงเหลือ"],
                                             "name": r["ชื่อวัสดุ"]}
                   for i, r in enumerate(records)}
    stock_keys = list(stock_index.keys())

    updates_qty, updates_date, details, skipped = [], [], [], []
    today = datetime.now().strftime("%Y-%m-%d")

    for sheet_name in _SHEET_STAFF:
        try:
            ws = src.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            continue
        for name, new_qty in _read_check_ws(ws):
            key = _norm(name)
            entry = stock_index.get(key)
            if entry is None and key in _ALIAS:
                entry = stock_index.get(_ALIAS[key])
            if entry is None:
                fk = difflib.get_close_matches(key, stock_keys, n=1, cutoff=0.80)
                if fk:
                    entry = stock_index[fk[0]]
            if entry:
                updates_qty.append({"range": f"{col_ltr}{entry['row']}", "values": [[new_qty]]})
                updates_date.append({"range": f"{col_date_ltr}{entry['row']}", "values": [[today]]})
                details.append({"ชื่อ": entry["name"], "เดิม": entry["cur_qty"], "ใหม่": new_qty,
                                 "เปลี่ยน": entry["cur_qty"] != new_qty})
            else:
                skipped.append(name)

    if updates_qty:
        dst.batch_update(updates_qty)
        dst.batch_update(updates_date)

    get_stock_df.clear()
    updated = sum(1 for d in details if d["เปลี่ยน"])
    return {"matched": len(details), "updated": updated,
            "skipped": len(skipped), "details": details, "skipped_names": skipped}


# ─── Local JSON fallback ──────────────────────────────────────────────────────

def _local_append(entry: dict):
    os.makedirs(os.path.dirname(LOCAL_HISTORY_FILE), exist_ok=True)
    records = _local_load()
    records.append(entry)
    with open(LOCAL_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _local_read() -> pd.DataFrame:
    records = _local_load()
    return pd.DataFrame(records) if records else _mock_history()


def _local_load() -> list:
    if os.path.exists(LOCAL_HISTORY_FILE):
        with open(LOCAL_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ─── Mock Data ────────────────────────────────────────────────────────────────

def _mock_stock() -> pd.DataFrame:
    return pd.DataFrame([
        {"ชื่อวัสดุ": "Composite Resin (Filtek Z350)",      "หน่วย": "กล่อง",   "คงเหลือ": 3,  "Reorder Point": 5,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Bonding Agent (Adper Single Bond)",  "หน่วย": "ขวด",     "คงเหลือ": 2,  "Reorder Point": 3,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Glass Ionomer Cement (Fuji IX)",     "หน่วย": "กระป๋อง", "คงเหลือ": 8,  "Reorder Point": 4,  "หมวดหมู่": "Restorative"},
        {"ชื่อวัสดุ": "Impression Material (Aquasil)",      "หน่วย": "กล่อง",   "คงเหลือ": 1,  "Reorder Point": 3,  "หมวดหมู่": "Impression"},
        {"ชื่อวัสดุ": "Lidocaine 2% (ยาชา)",                "หน่วย": "กล่อง",   "คงเหลือ": 12, "Reorder Point": 10, "หมวดหมู่": "Anesthetic"},
        {"ชื่อวัสดุ": "Gloves Size M",                      "หน่วย": "กล่อง",   "คงเหลือ": 4,  "Reorder Point": 5,  "หมวดหมู่": "PPE"},
        {"ชื่อวัสดุ": "Face Mask",                          "หน่วย": "กล่อง",   "คงเหลือ": 6,  "Reorder Point": 5,  "หมวดหมู่": "PPE"},
        {"ชื่อวัสดุ": "Etchant Gel 37%",                    "หน่วย": "หลอด",    "คงเหลือ": 7,  "Reorder Point": 4,  "หมวดหมู่": "Restorative"},
    ])


def _mock_history() -> pd.DataFrame:
    return pd.DataFrame([
        {"วันที่": "2026-05-10 09:15", "ประเภท": "รับเข้า",     "ชื่อวัสดุ": "Gloves Size M",                      "จำนวน": 5, "หมายเหตุ": "สั่งซื้อรายเดือน", "ผู้ทำรายการ": "นุ่น"},
        {"วันที่": "2026-05-11 10:30", "ประเภท": "อัพเดทสต้อค", "ชื่อวัสดุ": "Composite Resin (Filtek Z350)",     "จำนวน": 2, "หมายเหตุ": "3 → 2",            "ผู้ทำรายการ": "ปุ้ม"},
        {"วันที่": "2026-05-12 08:45", "ประเภท": "อัพเดทสต้อค", "ชื่อวัสดุ": "Lidocaine 2% (ยาชา)",              "จำนวน": 1, "หมายเหตุ": "12 → 1",           "ผู้ทำรายการ": "นุ่น"},
        {"วันที่": "2026-05-12 14:00", "ประเภท": "รับเข้า",     "ชื่อวัสดุ": "Bonding Agent (Adper Single Bond)", "จำนวน": 3, "หมายเหตุ": "สั่งซื้อเพิ่ม",   "ผู้ทำรายการ": "ปุ้ม"},
        {"วันที่": "2026-05-13 09:00", "ประเภท": "อัพเดทสต้อค", "ชื่อวัสดุ": "Face Mask",                         "จำนวน": 1, "หมายเหตุ": "6 → 1",            "ผู้ทำรายการ": "นุ่น"},
    ])
