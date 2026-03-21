import os
import json
import gspread
import uuid
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_NAME = os.getenv("SHEET_NAME", "Expense Bot")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

if not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("GOOGLE_CREDENTIALS_JSON topilmadi")

creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPE
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1


# 🔥 ID generator
def generate_id():
    return str(uuid.uuid4())[:8]


def add_expense(user_id, name, date, type_, amount, category, note):
    try:
        amount = int(float(amount))
    except Exception:
        amount = 0

    # 🔥 YANGI: ID yaratamiz
    row_id = generate_id()

    row = [
        row_id,  # 🔥 1-ustun
        str(user_id or ""),
        str(name or ""),
        str(date or ""),
        str(type_ or "expense"),
        amount,
        str(category or "Boshqa"),
        str(note or "")
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")

    # 🔥 keyin ishlatish uchun qaytaramiz
    return row_id


def update_expense(row_id, amount, category, note):
    records = sheet.get_all_records()

    for i, row in enumerate(records):
        if str(row.get("ID")) == str(row_id):
            row_number = i + 2  # header bor

            # F = Summa
            sheet.update(f"F{row_number}", amount)

            # G = Kategoriya
            sheet.update(f"G{row_number}", category)

            # H = Izoh
            sheet.update(f"H{row_number}", note)

            return True

    return False
