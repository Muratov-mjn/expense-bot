import os
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE", "expense-bot.json")
SHEET_NAME = os.getenv("SHEET_NAME", "Expense Bot")

creds = Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_FILE,
    scopes=SCOPE
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1


def add_expense(user_id, name, date, type_, amount, category, note):
    try:
        amount = int(float(amount))
    except Exception:
        amount = 0

    row = [
        str(user_id or ""),
        str(name or ""),
        str(date or ""),
        str(type_ or "expense"),
        amount,
        str(category or "Boshqa"),
        str(note or "")
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")
