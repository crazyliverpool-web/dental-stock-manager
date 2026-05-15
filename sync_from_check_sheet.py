"""
sync_from_check_sheet.py
ดึงจำนวนคงเหลือจาก sheet "เช็คสต๊อกรายเดือน เเต่ละบุคคล" แล้วอัพเดทลง Dental Stock
รองรับชื่อที่สะกดต่างกัน ด้วย fuzzy matching
"""

import re
import difflib
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES  = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDS   = "credentials/service_account.json"
SRC_ID  = "1TTjDAnrsRaUh-YHRzs3FHWKKhO8BExO5hYk-iwdSE9Y"
DST_ID  = "1A8ODOb_OsL7wYVmWESJE_SoEivb07K_avWIpYKqlTug"

SHEET_STAFF = {
    "อินอาร์ม": "อาร์ม",
    "พี่เปิ้ล":  "เปิ้ล",
    "ฮัน":       "ฮัน",
    "ฟีร่า":     "ฟีร่า",
    "กะมี":      "มี",
    "อิสสะห์":  "ซะห์",
    "ดารณี":     "ฉ้ะ",
}

QTY_COL_B = {"ฮัน", "อิสสะห์"}

# alias ที่รู้แน่ๆ ว่าต่างกัน: normalize(src_name) → normalize(dst_name)
ALIAS = {
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
    "hamonize a1e":                      "harmonize a1e",
    "hamonize a2e":                      "harmonize a2e",
    "hamonize a1d":                      "harmonize a1d",
    "hamonize a2d":                      "harmonize a2d",
    "hamonize a3d":                      "harmonize a3d",
    "filtek (z350) a1":                  "filtek z350 a1",
    "filtek (z350) a2":                  "filtek z350 a2",
    "filtek (z350) a3":                  "filtek z350 a3",
    "filtek (z350) a3.5":                "filtek z350 a3.5",
    "filtek (z350) a4":                  "filtek z350 a4",
    "filtek (z250) a3":                  "filtek z250 a3",
    "filtek (z250) a3.5":                "filtek z250 a3.5",
    "g-aenial universal (a2)":           "g-aenial universal a2",
    "g-aenial universal (a3)":           "g-aenial universal a3",
    "one bulk fill (flow a3)":           "one bulk fill flow a3",
    "clearfil flow (a1)":                "clearfil flow a1",
    "clearfil flow (a2)":                "clearfil flow a2",
    "clearfil flow (a3)":                "clearfil flow a3",
    "clearfil flow (a3.5)":              "clearfil flow a3.5",
    "clearfil flow (a4)":                "clearfil flow a4",
    "topicalยาชาสตอเบอร์รี่":           "topical ยาชาสตอเบอร์รี่",
    "ยาพาราแคพ500mg":                    "ยาพาราแคพ",
    "ยาพาราเซตามอล 500mg":              "ยาพาราแคพ",
    "ยาอม็อกซี่ 500mg":                 "ยาอม็อกซี่",
    "ไอบูโพรเฟน 400mg":                 "ไอบูโพรเฟน",
    "ซาร่าน้ำ เด็ก 120mg":              "ซาร่าน้ำ เด็ก",
    "3.5 fox":                           "retainer 3.5 fox",
    "3.5 monkey":                        "retainer 3.5 monkey",
    "3.5 penguin":                       "retainer 3.5 penguin",
    "6.5 fox":                           "retainer 6.5 fox",
    "5.0 fox":                           "retainer 5.0 fox",
    "3.5 rabbit":                        "retainer 3.5 rabbit",
    "bkt dtc ไม่มีฮุก":                 "bkt dtc ไม่มีฮุค",
    "bkt dtc มีฮุก":                    "bkt dtc มีฮุค",
    "bkt เกาหลี มีฮุก345":              "bkt เกาหลี มีฮุค 345",
    "bkt ao022":                         "bkt ao 022",
    "mbt 018ใหม่":                       "mbt 018 ใหม่",
    "ทิชชู่สเตอร์ไรด์":                 "ทิชชู่สเตอร์ไรล์",
    "ทิชชู่ใช้ในห้องน้ำ":               "ทิชชู่ห้องน้ำ",
    "พู่กันขาว (s)":                    "พู่กันขาว s",
    "พู่กันเหลือง (m)":                 "พู่กันเหลือง m",
    "พู่กันเขียว (l)":                  "พู่กันเขียว l",
    "เข็มสั้น":                         "เข็มถอนฟัน สั้น",
    "เข็มยาว":                          "เข็มถอนฟัน ยาว",
    "โซเดียม 5.25% ฟ้า":               "โซเดียมไฮเปอร์คลอไรท์ 5.25% ฟ้า",
    "โซเดียม 2.5% เขียว":              "โซเดียมไฮเปอร์คลอไรท์ 2.5% เขียว",
    "ไซริงค์ 10ml":                      "ไซริงค์พลาสติก 10ml",
    "ลวด 12 niti บน ":                  "ลวด 12 niti บน",
    "12 niti บน ":                       "ลวด 12 niti บน",
    "12 niti ล่าง":                      "ลวด 12 niti ล่าง",
    "14 niti บน ":                       "ลวด 14 niti บน",
    "14 niti ล่าง":                      "ลวด 14 niti ล่าง",
    "16 niti บน ":                       "ลวด 16 niti บน",
    "16 niti ล่าง":                      "ลวด 16 niti ล่าง",
    "18 niti บน ":                       "ลวด 18 niti บน",
    "18 niti ล่าง":                      "ลวด 18 niti ล่าง",
    "16x22 niti บน":                     "ลวด 16x22 niti บน",
    "16x22 niti ล่าง":                   "ลวด 16x22 niti ล่าง",
    "17x25 niti บน":                     "ลวด 17x25 niti บน",
    "17x25 niti ล่าง":                   "ลวด 17x25 niti ล่าง",
    "19x25 niti บน":                     "ลวด 19x25 niti บน",
    "19x25 niti ล่าง":                   "ลวด 19x25 niti ล่าง",
    "18 ss บน":                          "ลวด 18 ss บน",
    "18 ss ล่าง":                        "ลวด 18 ss ล่าง",
    "16x22 ss บน":                       "ลวด 16x22 ss บน",
    "16x22 ss ล่าง":                     "ลวด 16x22 ss ล่าง",
    "17x25 ss บน":                       "ลวด 17x25 ss บน",
    "17x25 ss ล่าง":                     "ลวด 17x25 ss ล่าง",
    "19x25 ss บน":                       "ลวด 19x25 ss บน",
    "19x25 ss ล่าง":                     "ลวด 19x25 ss ล่าง",
    "16x16 ss บน":                       "ลวด 16x16 ss บน",
    "12 se บน":                          "ลวด 12 se บน",
    "12 se ล่าง":                        "ลวด 12 se ล่าง",
    "14 se บน":                          "ลวด 14 se บน",
    "14 se ล่าง":                        "ลวด 14 se ล่าง",
    "16 se บน":                          "ลวด 16 se บน",
    "16 se ล่าง":                        "ลวด 16 se ล่าง",
    "18 se บน":                          "ลวด 18 se บน",
    "18 se ล่าง":                        "ลวด 18 se ล่าง",
    "19x25 se บน":                       "ลวด 19x25 se บน",
    "19x25 se ล่าง":                     "ลวด 19x25 se ล่าง",
    # ลวด ss (เขียน * แทน x, ไม่มี "ลวด" นำหน้า, ติดกัน)
    "18 ssล่าง":                         "ลวด 18 ss ล่าง",
    "16*22 ss บน":                       "ลวด 16x22 ss บน",
    "17*25 ss บน":                       "ลวด 17x25 ss บน",
    "19*25 ss บน":                       "ลวด 19x25 ss บน",
    "16*16 ss บน":                       "ลวด 16x16 ss บน",
    # ลวด se (ไม่มี "ลวด" นำหน้า, ติดกัน)
    "12seบน":                            "ลวด 12 se บน",
    "12seล่าง":                          "ลวด 12 se ล่าง",
    "14seบน":                            "ลวด 14 se บน",
    "14seล่าง":                          "ลวด 14 se ล่าง",
    "16seบน":                            "ลวด 16 se บน",
    "16seล่าง":                          "ลวด 16 se ล่าง",
    "18seบน":                            "ลวด 18 se บน",
    "18seล่าง":                          "ลวด 18 se ล่าง",
    "19*25seบน":                         "ลวด 19x25 se บน",
    "19*25seล่าง":                       "ลวด 19x25 se ล่าง",
    # g-aenial universal (มีวงเล็บ)
    "g-aenial universal (หลอดสีน้ำตาล) a2": "g-aenial universal a2",
    "g-aenial universal (หลอดสีน้ำตาล) a3": "g-aenial universal a3",
    # ปูนเขียว
    "ปูนเขียวลุง":                       "ปูนเขียว (alginate)",
    # misc
    "โซเดียมไฮเปอร์คลอไลท์ (เขียว) 2.5%": "โซเดียมไฮเปอร์คลอไรท์ 2.5% เขียว",
    "alcohol ขวดเล็ก/ขวดใหญ่":          "alcohol",
    "maks":                              "mask",
}


def parse_qty(s: str):
    m = re.search(r"\d+", str(s))
    return int(m.group()) if m else None


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def fuzzy_match(key: str, stock_keys: list, cutoff=0.75):
    matches = difflib.get_close_matches(key, stock_keys, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def read_src_items(ws) -> list:
    rows = ws.get_all_values()
    qty_col = 1 if ws.title in QTY_COL_B else 2
    items = []
    for row in rows[1:]:
        if len(row) <= qty_col:
            continue
        name = row[0].strip()
        if not name:
            continue
        qty = parse_qty(row[qty_col])
        if qty is not None:
            items.append((name, qty))
    return items


def run(dry_run: bool = True):
    creds = Credentials.from_service_account_file(CREDS, scopes=SCOPES)
    gc    = gspread.authorize(creds)

    src = gc.open_by_key(SRC_ID)
    dst = gc.open_by_key(DST_ID).worksheet("Stock")

    records  = dst.get_all_records()
    headers  = dst.row_values(1)
    col_qty  = headers.index("คงเหลือ") + 1
    col_date = headers.index("วันที่เช็คล่าสุด") + 1
    col_ltr      = gspread.utils.rowcol_to_a1(1, col_qty).rstrip("0123456789")
    col_date_ltr = gspread.utils.rowcol_to_a1(1, col_date).rstrip("0123456789")

    stock_index = {}
    for i, r in enumerate(records):
        key = normalize(r["ชื่อวัสดุ"])
        stock_index[key] = {"row": i + 2, "cur_qty": r["คงเหลือ"],
                            "name": r["ชื่อวัสดุ"]}
    stock_keys = list(stock_index.keys())

    updates_qty  = []
    updates_date = []
    matched      = []
    unmatched    = []
    today = datetime.now().strftime("%Y-%m-%d")

    for sheet_name, staff in SHEET_STAFF.items():
        try:
            ws = src.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"⚠️  ไม่พบ worksheet: {sheet_name}")
            continue

        items = read_src_items(ws)
        for name, new_qty in items:
            key = normalize(name)

            # 1. exact match
            entry = stock_index.get(key)
            match_type = "exact"

            # 2. alias
            if entry is None and key in ALIAS:
                alias_key = ALIAS[key]
                entry = stock_index.get(alias_key)
                match_type = "alias"

            # 3. ขนาด X*Y → รากเทียม bd XxY (implant sizes)
            if entry is None:
                m = re.match(r'^ขนาด (\d+\.?\d*)\*(\d+\.?\d*)$', key)
                if m:
                    entry = stock_index.get(f'รากเทียม bd {m.group(1)}x{m.group(2)}')
                    if entry:
                        match_type = "implant-pattern"

            # 4. fuzzy
            if entry is None:
                fkey = fuzzy_match(key, stock_keys, cutoff=0.80)
                if fkey:
                    entry = stock_index[fkey]
                    match_type = f"fuzzy({fkey})"

            if entry:
                row = entry["row"]
                updates_qty.append({"range": f"{col_ltr}{row}", "values": [[new_qty]]})
                updates_date.append({"range": f"{col_date_ltr}{row}", "values": [[today]]})
                matched.append((sheet_name, name, entry["name"],
                                entry["cur_qty"], new_qty, match_type))
            else:
                unmatched.append((sheet_name, name, new_qty))

    # ─── รายงาน ────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"✅ จับคู่ได้:       {len(matched)} รายการ")
    print(f"❌ ไม่พบใน Stock:  {len(unmatched)} รายการ")
    print(f"{'='*60}\n")

    print("── รายการที่จะอัพเดท ──")
    for sheet, src_name, dst_name, old, new, mtype in matched:
        flag = "  " if str(old) == str(new) else "→"
        note = f"  [{mtype}]" if mtype != "exact" else ""
        print(f"  [{sheet}] {dst_name}: {old} {flag} {new}{note}")

    if unmatched:
        print(f"\n── ข้ามไป (ชื่อไม่ตรง) ──")
        for sheet, name, qty in unmatched:
            print(f"  [{sheet}] {name}  qty={qty}")

    if dry_run:
        print("\n⚠️  DRY RUN — ยังไม่ได้เขียนลง Sheet")
        print("   รัน:  python3 sync_from_check_sheet.py --write")
        return

    if updates_qty:
        dst.batch_update(updates_qty)
        dst.batch_update(updates_date)
        print(f"\n✅ อัพเดทสำเร็จ {len(updates_qty)} รายการ")
    else:
        print("\nไม่มีรายการที่ต้องอัพเดท")


if __name__ == "__main__":
    import sys
    dry = "--write" not in sys.argv
    run(dry_run=dry)
