from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

import os
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from sheets import add_expense

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# 🔥 STATE
user_state = {}

# 🔥 CLEAN CHAT STORAGE
user_messages = {}


def save_msg(user_id, msg_id):
    user_messages.setdefault(user_id, []).append(msg_id)


async def clear_chat(context, chat_id, user_id):
    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except:
                pass
        user_messages[user_id] = []


# 🔘 MENULAR
start_menu = [["🚀 Start"]]

main_menu = [["Daromadlar", "Xarajatlar"]]

income_menu = [
    ["Oylik maosh", "Mukofotlar"],
    ["Shartnoma", "Frilans"],
    ["Keshbek", "Divident"],
    ["Bira", "Kredit"],
    ["Qarz"]
]

expense_menu = [
    ["Jamshid", "Investitsiya"],
    ["Kreditga", "Shahzod"],
    ["Dinara", "Go'zaloyga"],
    ["Boshqa harakatlar"],
    ["Yig‘ishga", "Qarz"]
]

cancel_btn = [["❌ Bekor qilish"]]
confirm_btn = [["✅ Kiritish", "❌ Bekor qilish"]]


# 🔥 PARSER
def parse_amount(text):
    text = text.lower()

    if "k" in text:
        return int(re.findall(r'\d+', text)[0]) * 1000

    if "ming" in text:
        return int(re.findall(r'\d+', text)[0]) * 1000

    if "mln" in text:
        return int(re.findall(r'\d+', text)[0]) * 1000000

    return int(re.findall(r'\d+', text)[0])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "🚀 Boshlash uchun tugmani bosing",
        reply_markup=ReplyKeyboardMarkup(start_menu, resize_keyboard=True)
    )
    save_msg(update.message.from_user.id, msg.message_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    user_id = user.id
    name = user.first_name
    text = update.message.text.strip()

    save_msg(user_id, update.message.message_id)

    # ❌ BEKOR
    if text == "❌ Bekor qilish":
        user_state.pop(user_id, None)
        await clear_chat(context, update.effective_chat.id, user_id)

        msg = await update.message.reply_text(
            "🚀 Start",
            reply_markup=ReplyKeyboardMarkup(start_menu, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🚀 START BOSILDI
    if text == "🚀 Start":
        msg = await update.message.reply_text(
            "📊 Tanlang:",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🔹 BOSHLANG‘ICH
    if text == "Daromadlar":
        user_state[user_id] = {"type": "income"}

        msg = await update.message.reply_text(
            "📥 Daromad turini tanlang:",
            reply_markup=ReplyKeyboardMarkup(income_menu, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    if text == "Xarajatlar":
        user_state[user_id] = {"type": "expense"}

        msg = await update.message.reply_text(
            "📤 Xarajat turini tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                expense_menu, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🔹 KATEGORIYA
    if user_id in user_state and "category" not in user_state[user_id]:
        user_state[user_id]["category"] = text
        user_state[user_id]["step"] = "note"

        msg = await update.message.reply_text(
            "✏️ Izoh yozing:",
            reply_markup=ReplyKeyboardMarkup(cancel_btn, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🔹 IZOH
    if user_id in user_state and user_state[user_id].get("step") == "note":
        user_state[user_id]["note"] = text
        user_state[user_id]["step"] = "amount"

        msg = await update.message.reply_text(
            "💰 Summani kiriting:",
            reply_markup=ReplyKeyboardMarkup(cancel_btn, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🔹 SUMMA
    if user_id in user_state and user_state[user_id].get("step") == "amount":

        if not re.search(r'\d+', text):
            msg = await update.message.reply_text("❗ To‘g‘ri summa kiriting (masalan: 50k)")
            save_msg(user_id, msg.message_id)
            return

        amount = parse_amount(text)

        user_state[user_id]["amount"] = amount
        user_state[user_id]["step"] = "confirm"

        data = user_state[user_id]

        msg = await update.message.reply_text(
            f"📌 {data['category']}\n"
            f"📝 {data['note']}\n"
            f"💰 {amount} so'm\n\n"
            "Tasdiqlaysizmi?",
            reply_markup=ReplyKeyboardMarkup(confirm_btn, resize_keyboard=True)
        )
        save_msg(user_id, msg.message_id)
        return

    # 🔹 TASDIQLASH
    if user_id in user_state and user_state[user_id].get("step") == "confirm":

        if text == "✅ Kiritish":
            data = user_state[user_id]
            today = datetime.now().strftime("%Y-%m-%d")

            add_expense(
                user_id=user_id,
                name=name,
                date=today,
                type_=data["type"],
                amount=data["amount"],
                category=data["category"],
                note=data["note"]
            )

            await clear_chat(context, update.effective_chat.id, user_id)

            msg = await update.message.reply_text(
                "🚀 Start",
                reply_markup=ReplyKeyboardMarkup(
                    start_menu, resize_keyboard=True)
            )
            save_msg(user_id, msg.message_id)

            user_state.pop(user_id)
            return


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
