import re


def parse_expense(text):

    amount = re.findall(r'\d+', text)
    amount = int(amount[0]) if amount else 0

    income_words = ["oylik", "maosh", "bonus", "daromad"]

    type_ = "expense"

    for word in income_words:
        if word in text.lower():
            type_ = "income"

    note = text.replace(str(amount), "").strip()

    return {
        "type": type_,
        "amount": amount,
        "note": note
    }
