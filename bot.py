from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from ai_parser import parse_with_ai
from sheets import add_expense

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

ALLOWED_USERS = [
    int(user_id.strip())
    for user_id in os.getenv("ALLOWED_USERS", "").split(",")
    if user_id.strip().isdigit()
]


def normalize_expenses(parsed_data):
    if parsed_data is None:
        return []

    if isinstance(parsed_data, dict):
        return [parsed_data]

    if isinstance(parsed_data, list):
        return [item for item in parsed_data if isinstance(item, dict)]

    return []


def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Sizga bu botdan foydalanishga ruxsat yo'q.")
        return

    await update.message.reply_text(
        "🤖 Expense Bot ishlayapti.\n\n"
        "Harajatlaringizni yozib boring, men ularni saqlab boraman."
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Sizga bu botdan foydalanishga ruxsat yo'q.")
        return

    await update.message.reply_text(
        f"👤 Ism: {user.first_name}\n🆔 User ID: {user.id}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    name = user.first_name
    text = (update.message.text or "").strip()

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Sizga bu botdan foydalanishga ruxsat yo'q.")
        return

    try:
        today = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")

        parsed = parse_with_ai(text, today=today)
        expenses = normalize_expenses(parsed)

        if not expenses:
            await update.message.reply_text(
                "⚠️ Xarajatni tushunmadim. Qayta aniqroq yozib ko'ring."
            )
            return

        saved_items = []
        skipped_count = 0
        total_amount = 0

        for item in expenses:
            if not isinstance(item, dict):
                skipped_count += 1
                continue

            type_ = item.get("type", "expense")
            amount = item.get("amount", 0)
            category = item.get("category", "Boshqa")
            note = item.get("note", text)
            item_date = item.get("date") or today

            if not is_valid_date(item_date):
                item_date = today

            try:
                amount = int(float(amount))
            except Exception:
                amount = 0

            if amount <= 0:
                skipped_count += 1
                continue

            add_expense(
                user_id=user_id,
                name=name,
                date=item_date,
                type_=type_,
                amount=amount,
                category=category,
                note=note
            )

            total_amount += amount
            saved_items.append(
                f"{len(saved_items)+1}) {category} — {amount} so'm\n"
                f"   Izoh: {note}\n"
                f"   Sana: {item_date}"
            )

        if not saved_items:
            await update.message.reply_text(
                "⚠️ Xarajatlar topildi, lekin summalar noto'g'ri bo'lgani uchun saqlanmadi."
            )
            return

        reply = (
            f"✅ {len(saved_items)} ta xarajat saqlandi.\n\n"
            + "\n".join(saved_items)
            + f"\n\n💰 Jami: {total_amount} so'm"
        )

        if skipped_count > 0:
            reply += f"\n\n⚠️ {skipped_count} ta yozuv tashlab ketildi."

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(
            "⚠️ Xatolik yuz berdi. Qayta urinib ko'ring."
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", my_id))
app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
