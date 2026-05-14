"""
migrate_from_check_sheet.py
รันครั้งเดียว — ล้าง Stock sheet แล้ว import ข้อมูลจากไฟล์เช็คสต๊อกรายเดือน
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDS  = os.getenv("CREDENTIALS_PATH", "credentials/service_account.json")
SHEET_ID = os.getenv("SHEET_ID", "")

# ─── ข้อมูลทั้งหมด แยกตามพนักงาน ──────────────────────────────────────────
# format: (ชื่อวัสดุ, หน่วย, คงเหลือ, reorder_point, หมวดหมู่, ผู้รับผิดชอบ)

STOCK_DATA = [

    # ══════════════════ อาร์ม — วัสดุอุดฟัน ══════════════════
    ("บอนดิ้งอุดฟัน ขวดส้ม",                     "ขวด",   5,  2,  "Restorative",  "อาร์ม"),
    ("บอนดิ้งไบท์ (ขวดเหลือง)",                   "ขวด",   1,  2,  "Restorative",  "อาร์ม"),
    ("บอนดิ้ง Optibal Universal Solo",             "ขวด",   1,  2,  "Restorative",  "อาร์ม"),
    ("บอนดิ้งติดเครื่องมือ SoLo",                  "ขวด",  13,  3,  "Restorative",  "อาร์ม"),
    ("บอนดิ้งติดเครื่องมือ 3M",                    "ขวด",   3,  2,  "Restorative",  "อาร์ม"),
    ("เอชชิ่ง Fine Etch37 หลอดเขียว",              "หลอด", 11,  5,  "Restorative",  "อาร์ม"),
    ("Ultra-Etch เอชชิ้งหลอดสีฟ้า",               "หลอด", 13,  5,  "Restorative",  "อาร์ม"),
    ("เอชชิ้งกรด (ครอบฟัน)",                       "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("Gren Gloo กาวหลอดสีเขียว",                   "หลอด",  7,  3,  "Restorative",  "อาร์ม"),
    ("Transbond กาว 3M ติดเครื่องมือ",             "หลอด", 22,  5,  "Orthodontic",  "อาร์ม"),
    ("Bite",                                        "หลอด", 22,  5,  "Restorative",  "อาร์ม"),
    ("Flow ธรรมดา",                                 "หลอด",  8,  3,  "Restorative",  "อาร์ม"),
    ("บล็อกเหงือกฟอกสีฟัน",                        "หลอด",  6,  3,  "Restorative",  "อาร์ม"),
    ("Sealant",                                     "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("N Flow A1",                                   "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("N Flow A2",                                   "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("N Flow A3",                                   "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("N Flow A3.5",                                 "หลอด",  7,  2,  "Restorative",  "อาร์ม"),
    ("Flowable Filtek 3M A3",                       "หลอด",  7,  3,  "Restorative",  "อาร์ม"),
    ("Harmonize A1E",                               "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Harmonize A2E",                               "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Harmonize A1D",                               "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Harmonize A2D",                               "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Harmonize A3D",                               "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z350 A1",                              "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z350 A2",                              "หลอด",  6,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z350 A3",                              "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z350 A3.5",                            "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z350 A4",                              "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z250 A3",                              "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Z250 A3.5",                            "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Estelite Equick A2",                          "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("Estelite Equick A3",                          "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial A1",                                 "หลอด",  0,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial A2",                                 "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial A3",                                 "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial A3.5",                               "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial A4",                                 "หลอด",  0,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial Universal A2",                       "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("G-aenial Universal A3",                       "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("One Bulk Fill Flow A3",                       "หลอด", 10,  3,  "Restorative",  "อาร์ม"),
    ("Bulk Fill ธรรมดา A3",                         "หลอด",  0,  2,  "Restorative",  "อาร์ม"),
    ("Clearfil Flow A1",                            "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("Clearfil Flow A2",                            "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("Clearfil Flow A3",                            "หลอด",  7,  2,  "Restorative",  "อาร์ม"),
    ("Clearfil Flow A3.5",                          "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Clearfil Flow A4",                            "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("CLEARFIL AP-X A2",                            "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("CLEARFIL AP-X A3",                            "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("CLEARFIL AP-X A3.5",                          "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("CLEARFIL AP-X A4",                            "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Solare หลอดสีส้ม",                            "หลอด",  0,  2,  "Restorative",  "อาร์ม"),
    ("UL",                                          "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("U",                                           "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("ES2 A2",                                      "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("ES2 A3.5",                                    "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Tem-It หลอดสีเหลือง",                         "หลอด",  4,  2,  "Restorative",  "อาร์ม"),
    ("NX3",                                         "กล่อง",  1,  1,  "Restorative",  "อาร์ม"),
    ("Filtek Bright",                               "หลอด",  1,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Warm",                                 "หลอด",  3,  2,  "Restorative",  "อาร์ม"),
    ("Filtek Natural",                              "หลอด",  2,  2,  "Restorative",  "อาร์ม"),
    ("Optibal FL",                                  "กล่อง",  1,  1,  "Restorative",  "อาร์ม"),
    ("SE Bond",                                     "กล่อง",  1,  1,  "Restorative",  "อาร์ม"),
    ("แคลเซียม",                                    "หลอด",  6,  3,  "Restorative",  "อาร์ม"),
    ("Topical ยาชาสตอเบอร์รี่",                     "กระปุก", 1, 1,  "Medication",   "อาร์ม"),
    ("สต็อปบีท",                                    "ขวด",   1,  1,  "Restorative",  "อาร์ม"),
    ("เจลโฟม",                                      "กระปุก", 2, 1,  "Restorative",  "อาร์ม"),
    ("เควิท",                                       "กระปุก", 4, 2,  "Restorative",  "อาร์ม"),
    ("ไซเลน",                                       "ขวด",   2,  1,  "Restorative",  "อาร์ม"),
    ("โมโนบอล",                                     "ขวด",   1,  1,  "Restorative",  "อาร์ม"),
    ("Biodentine",                                  "อัน",   3,  2,  "Restorative",  "อาร์ม"),
    ("Dentine Conditioner",                         "ขวด",   2,  1,  "Restorative",  "อาร์ม"),
    ("เอชชิ้ง จัมโบ้ แบบเติม",                      "หลอด",  5,  2,  "Restorative",  "อาร์ม"),
    ("ไหมเย็บแผล Nylon 4-0",                        "กล่อง",  0,  1,  "Surgical",     "อาร์ม"),
    ("ไหมเย็บแผล Nylon 6-0",                        "กล่อง",  2,  1,  "Surgical",     "อาร์ม"),
    ("ไหมเย็บแผล Novasorb 4-0",                     "กล่อง",  1,  1,  "Surgical",     "อาร์ม"),
    ("ไหมเย็บแผล Novasorb 5-0",                     "กล่อง",  2,  1,  "Surgical",     "อาร์ม"),
    ("ไหมขาว",                                      "ชิ้น",  0,  2,  "Surgical",     "อาร์ม"),
    ("เมมเบรน Osteo Bio Evolution",                 "กล่อง",  2,  1,  "Surgical",     "อาร์ม"),
    ("กระดูกเทียม Cerabone Plus",                   "กล่อง",  3,  1,  "Surgical",     "อาร์ม"),
    ("กระดูกเทียม S1",                              "กล่อง",  2,  1,  "Surgical",     "อาร์ม"),
    ("กระดูกเทียม Inter Oss",                       "กล่อง",  1,  1,  "Surgical",     "อาร์ม"),
    ("กระดูกเทียม ไฮดอกซี่",                        "กล่อง",  4,  1,  "Surgical",     "อาร์ม"),

    # ══════════════════ เปิ้ล — ลวดจัดฟัน ══════════════════
    ("ลวด 12 Niti บน",    "เส้น", 300, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 12 Niti ล่าง",  "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 14 Niti บน",    "เส้น", 500, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 14 Niti ล่าง",  "เส้น", 600, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16 Niti บน",    "เส้น", 600, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16 Niti ล่าง",  "เส้น", 300, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 Niti บน",    "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 Niti ล่าง",  "เส้น", 300, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16x22 Niti บน", "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16x22 Niti ล่าง","เส้น",400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 17x25 Niti บน", "เส้น", 600, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 17x25 Niti ล่าง","เส้น",600, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 Niti บน", "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 Niti ล่าง","เส้น",200, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 SS บน",      "เส้น", 300, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 SS ล่าง",    "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16x22 SS บน",   "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16x22 SS ล่าง", "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 17x25 SS บน",   "เส้น", 200, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 17x25 SS ล่าง", "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 SS บน",   "เส้น", 400, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 SS ล่าง", "เส้น", 300, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 16x16 SS บน",   "เส้น", 200, 100, "Orthodontic", "เปิ้ล"),
    ("ลวด 12 SE บน",      "เส้น", 200,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 12 SE ล่าง",    "เส้น", 300,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 14 SE บน",      "เส้น", 100,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 14 SE ล่าง",    "เส้น", 400,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 16 SE บน",      "เส้น", 150,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 16 SE ล่าง",    "เส้น", 200,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 SE บน",      "เส้น", 400,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 18 SE ล่าง",    "เส้น", 100,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 SE บน",   "เส้น", 400,  50, "Orthodontic", "เปิ้ล"),
    ("ลวด 19x25 SE ล่าง", "เส้น", 200,  50, "Orthodontic", "เปิ้ล"),

    # ══════════════════ กะละห์ — PPE / น้ำยา ══════════════════
    ("ถุงมือ XS",                               "ลัง",    4,  1,  "PPE",          "กะละห์"),
    ("ถุงมือ S",                                "ลัง",    2,  1,  "PPE",          "กะละห์"),
    ("ทิชชู่สเตอร์ไรล์",                        "กระปุก",15,  5,  "PPE",          "กะละห์"),
    ("ทิชชู่ห้องน้ำ",                           "แพ็ค",   6,  3,  "PPE",          "กะละห์"),
    ("หมวกหมอ",                                 "ห่อ",    8,  3,  "PPE",          "กะละห์"),
    ("ผ้าก๊อส",                                 "ลัง",    1,  1,  "PPE",          "กะละห์"),
    ("สำลี",                                    "ห่อ",    1,  1,  "PPE",          "กะละห์"),
    ("ยาสีฟัน ฟลูโอคาริล ฟ้า",                  "กล่อง", 54, 20, "Patient Products","กะละห์"),
    ("ยาสีฟัน ฟลูโอคาริล ชมพู",                 "กล่อง", 66, 20, "Patient Products","กะละห์"),
    ("แปรงซอกฟัน เบอร์ 2",                      "กล่อง",  6,  3,  "Patient Products","กะละห์"),
    ("แปรงซอกฟัน เบอร์ 3",                      "กล่อง", 19,  5,  "Patient Products","กะละห์"),
    ("ไหมขัดฟัน",                               "อัน",   37, 10,  "Patient Products","กะละห์"),
    ("แปรงสีฟันจัดฟัน",                         "อัน",  168, 50,  "Patient Products","กะละห์"),
    ("น้ำยาบ้วนปาก ฟลูโอคาริล",                 "ขวด",   12,  5,  "Patient Products","กะละห์"),
    ("ถุงดำขยะ ใหญ่",                           "ลัง",    1,  1,  "Cleaning",     "กะละห์"),
    ("ถุงดำขยะ เล็ก",                           "ม้วน",   5,  2,  "Cleaning",     "กะละห์"),
    ("ถุงฆ่าเชื้อ",                              "แพ็ค",   3,  1,  "Cleaning",     "กะละห์"),
    ("ถุงเล็กยูนิต",                             "แพ็ค",   3,  1,  "PPE",          "กะละห์"),
    ("ถุงเล็กห้องเอกซ์เรย์",                    "แพ็ค",   5,  2,  "PPE",          "กะละห์"),
    ("ผงซักฟอก",                                "ห่อ",    4,  2,  "Cleaning",     "กะละห์"),
    ("ปูนเขียว (Alginate)",                      "ถุง",    4,  5,  "Impression",   "กะละห์"),
    ("ปูนออจิเนต (ปูนม่วง)",                     "ถุง",   32, 10,  "Impression",   "กะละห์"),
    ("น้ำยาล้างห้องน้ำ",                         "ขวด",    5,  2,  "Cleaning",     "กะละห์"),
    ("ซันไล",                                   "ถุง",   12,  5,  "Cleaning",     "กะละห์"),
    ("ฟองน้ำ สก๊อตไบร์ท",                        "อัน",    4,  2,  "Cleaning",     "กะละห์"),
    ("น้ำยาแช่เครื่องมือ/ดูดซักชั่น",            "ขวด",    0,  2,  "Cleaning",     "กะละห์"),
    ("สเปรย์ฉีดห้องน้ำ/ในห้อง",                  "ขวด",    6,  2,  "Cleaning",     "กะละห์"),
    ("หลอดดูดซักชั่น",                          "ลัง",    2,  1,  "PPE",          "กะละห์"),
    ("ผงแช่เทรย์",                              "กระปุก",  2,  1,  "Cleaning",     "กะละห์"),
    ("แอลกอฮอล์ จุดไฟ",                         "ขวด",    4,  2,  "Cleaning",     "กะละห์"),

    # ══════════════════ ฟีร่า — ยา / Bracket / สกรู ══════════════════
    ("ยาพาราแคพ",                               "กล่อง", 11,  5,  "Medication",   "ฟีร่า"),
    ("ยาอม็อกซี่",                               "กล่อง",  1,  2,  "Medication",   "ฟีร่า"),
    ("ไอบูโพรเฟน",                               "กล่อง",  2,  2,  "Medication",   "ฟีร่า"),
    ("ซาร่าน้ำ เด็ก",                            "กล่อง",  4,  2,  "Medication",   "ฟีร่า"),
    ("แปรงขัดซอกฟัน N.3",                        "กล่อง", 18,  5,  "Patient Products","ฟีร่า"),
    ("แปรงขัดซอกฟัน N.2",                        "กล่อง",  7,  3,  "Patient Products","ฟีร่า"),
    ("Retainer 3.5 Fox",                         "กล่อง", 14,  5,  "Orthodontic",  "ฟีร่า"),
    ("Retainer 3.5 Monkey",                      "กล่อง",  9,  5,  "Orthodontic",  "ฟีร่า"),
    ("Retainer 3.5 Penguin",                     "กล่อง",  5,  3,  "Orthodontic",  "ฟีร่า"),
    ("Retainer 6.5 Fox",                         "กล่อง",  3,  2,  "Orthodontic",  "ฟีร่า"),
    ("Retainer 5.0 Fox",                         "กล่อง",  1,  2,  "Orthodontic",  "ฟีร่า"),
    ("Retainer 3.5 Rabbit",                      "กล่อง",  4,  2,  "Orthodontic",  "ฟีร่า"),
    ("BKT DTC ไม่มีฮุค",                         "แพ็ค",  40, 10,  "Orthodontic",  "ฟีร่า"),
    ("BKT DTC มีฮุค",                            "แพ็ค",  30, 10,  "Orthodontic",  "ฟีร่า"),
    ("BKT เกาหลี มีฮุค 345",                     "แพ็ค",   0,  5,  "Orthodontic",  "ฟีร่า"),
    ("BKT เกาหลี 018",                           "แพ็ค",  20,  5,  "Orthodontic",  "ฟีร่า"),
    ("ฟอกสีฟัน Zoom",                            "กล่อง",  4,  2,  "Restorative",  "ฟีร่า"),
    ("BKT AO 022",                               "แพ็ค",  70, 15,  "Orthodontic",  "ฟีร่า"),
    ("MBT 018 ใหม่",                              "แพ็ค",  60, 15,  "Orthodontic",  "ฟีร่า"),
    ("MBT Slot 018 BKT",                         "กล่อง",  3,  1,  "Orthodontic",  "ฟีร่า"),
    ("สกรู 1.6x6",                               "กล่อง", 55, 10,  "Orthodontic",  "ฟีร่า"),
    ("สกรู 1.6x8",                               "กล่อง", 22, 10,  "Orthodontic",  "ฟีร่า"),
    ("สกรู 1.6x10",                              "กล่อง", 20, 10,  "Orthodontic",  "ฟีร่า"),
    ("ถุงมือ XS (ฟีร่า)",                        "ลัง",    9,  2,  "PPE",          "ฟีร่า"),
    ("ถุงมือ S (ฟีร่า)",                         "ลัง",    3,  2,  "PPE",          "ฟีร่า"),

    # ══════════════════ ซะห์ — ยาชา / เข็ม / วัสดุทั่วไป ══════════════════
    ("พู่กันขาว S",                              "กระปุก",  2,  1,  "Instruments",  "ซะห์"),
    ("พู่กันเหลือง M",                           "กระปุก",  8,  2,  "Instruments",  "ซะห์"),
    ("พู่กันเขียว L",                            "กระปุก",  4,  2,  "Instruments",  "ซะห์"),
    ("พู่กันส้ม",                                "กระปุก",  8,  2,  "Instruments",  "ซะห์"),
    ("Blade 12",                                 "กล่อง",   4,  2,  "Instruments",  "ซะห์"),
    ("Blade 15",                                 "กล่อง",   3,  2,  "Instruments",  "ซะห์"),
    ("Blade 15C",                                "กล่อง",   2,  2,  "Instruments",  "ซะห์"),
    ("เข็มไซริงค์พลาสติก สีส้ม",                 "กล่อง",   6,  2,  "Instruments",  "ซะห์"),
    ("เข็มไซริงค์พลาสติก สีเขียว",               "กล่อง",   6,  2,  "Instruments",  "ซะห์"),
    ("เข็มไซริงค์พลาสติก สีเทา",                 "กล่อง",   9,  3,  "Instruments",  "ซะห์"),
    ("เข็มไซริงค์พลาสติก สีชมพู",                "กล่อง",   7,  3,  "Instruments",  "ซะห์"),
    ("ยาชา 2%",                                  "กล่อง",  19,  5,  "Medication",   "ซะห์"),
    ("ยาชา 4%",                                  "กล่อง",  22,  5,  "Medication",   "ซะห์"),
    ("เข็มถอนฟัน สั้น",                          "กล่อง",  14,  5,  "Instruments",  "ซะห์"),
    ("เข็มถอนฟัน ยาว",                           "กล่อง",   7,  3,  "Instruments",  "ซะห์"),
    ("กระดาษฟิล์ม",                              "กล่อง",   6,  2,  "Instruments",  "ซะห์"),
    ("ซองฟิล์ม",                                 "กล่อง",  10,  3,  "Instruments",  "ซะห์"),
    ("โซเดียมไฮเปอร์คลอไรท์ 5.25% ฟ้า",         "ขวด",    3,  2,  "Cleaning",     "ซะห์"),
    ("โซเดียมไฮเปอร์คลอไรท์ 2.5% เขียว",        "ขวด",    6,  2,  "Cleaning",     "ซะห์"),
    ("EDTA",                                     "ขวด",    2,  1,  "Restorative",  "ซะห์"),
    ("ไซริงค์พลาสติก 10ml",                      "ลัง",    3,  1,  "Instruments",  "ซะห์"),
    ("Chlorhexidine",                            "ขวด",    3,  1,  "Medication",   "ซะห์"),
    ("แผ่นรับเบอร์แดมชีท",                       "กล่อง",   5,  2,  "Instruments",  "ซะห์"),
    ("Alcohol",                                  "ขวด",   24,  5,  "Cleaning",     "ซะห์"),
    ("คาคีไวท์",                                 "ขวด",   13,  5,  "Cleaning",     "ซะห์"),
    ("ผ้าก๊อซ",                                  "แพ็ค", 150, 20,  "PPE",          "ซะห์"),
    ("ถุงมือ Sterile S",                         "กล่อง",   2,  1,  "PPE",          "ซะห์"),
    ("ถุงมือ Sterile XS",                        "กล่อง",   1,  1,  "PPE",          "ซะห์"),
    ("Normal Saline เล็ก",                       "ชิ้น",   16,  5,  "Medication",   "ซะห์"),
    ("Normal Saline ใหญ่",                       "ขวด",   26,  5,  "Medication",   "ซะห์"),
    ("Floss ขาว",                                "ชิ้น",    8,  3,  "Patient Products","ซะห์"),
    ("Floss เทา",                                "ชิ้น",    6,  3,  "Patient Products","ซะห์"),
    ("แปรงซอกฟัน ไซส์ 2",                        "กล่อง", 278, 20,  "Patient Products","ซะห์"),
    ("แปรงซอกฟัน ไซส์ 3",                        "กล่อง",  16,  5,  "Patient Products","ซะห์"),
    ("แปรงจัดฟัน",                               "ลัง",    5,  1,  "Patient Products","ซะห์"),
    ("ยาสีฟันจัดฟัน",                            "แพ็ค",  20,  5,  "Patient Products","ซะห์"),
    ("น้ำยาบ้วนปาก",                             "แพ็ค",  21,  5,  "Patient Products","ซะห์"),
    ("น้ำยาล้างมือ Kerei",                        "ถุง",    8,  3,  "Cleaning",     "ซะห์"),
    ("ขี้ผึ้ง",                                   "กล่อง",  3,  1,  "Medication",   "ซะห์"),
    ("Mask",                                     "ลัง",    4,  1,  "PPE",          "ซะห์"),
    ("Mask 3M",                                  "กล่อง",  4,  1,  "PPE",          "ซะห์"),
    ("Optragate S",                              "ชิ้น",   33,  5,  "Instruments",  "ซะห์"),
    ("Optragate M",                              "ชิ้น",   15,  5,  "Instruments",  "ซะห์"),
    ("ถุงดำ เล็ก",                               "ม้วน",  14,  3,  "Cleaning",     "ซะห์"),
    ("ถุงดำ ใหญ่",                               "ม้วน",  32,  5,  "Cleaning",     "ซะห์"),
    ("ถุงแดง",                                   "แพ็ค",  12,  3,  "Cleaning",     "ซะห์"),
    ("อะติเนท",                                  "ถุง",   19,  5,  "Restorative",  "ซะห์"),
]


def run():
    creds = Credentials.from_service_account_file(CREDS, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    ws    = gc.open_by_key(SHEET_ID).worksheet("Stock")

    # ล้างข้อมูลเก่า (เก็บ header)
    existing = ws.get_all_values()
    if len(existing) > 1:
        ws.delete_rows(2, len(existing))
        print(f"ลบ {len(existing)-1} แถวเดิมออกแล้ว")

    # เขียนข้อมูลใหม่ทีเดียว
    rows = [list(row) + [""] for row in STOCK_DATA]  # เพิ่ม col G (วันที่เช็ค) ว่าง
    ws.append_rows(rows, value_input_option="RAW")

    print(f"✓ Import สำเร็จ — {len(rows)} รายการ")

    # สรุปต่อพนักงาน
    from collections import Counter
    counts = Counter(r[5] for r in STOCK_DATA)
    for name, cnt in sorted(counts.items()):
        print(f"  {name}: {cnt} รายการ")


if __name__ == "__main__":
    run()
