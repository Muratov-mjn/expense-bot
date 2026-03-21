import re

CATEGORIES = {
    "food": ["bozor", "go‘sht", "non", "ovqat", "choy", "market"],
    "transport": ["taksi", "taxi", "bus", "metro", "benzin"],
    "home": ["ijara", "kvartira", "gaz", "svet", "elektr"],
    "health": ["dorixona", "dori", "shifoxona"],
    "education": ["kurs", "maktab", "kitob"],
    "entertainment": ["kino", "dam", "o‘yin", "kafe"],
}

FAMILY_WORDS = ["ona", "onam", "aka", "uka", "dadam", "singil", "opa"]


def extract_amount(text):
    text = text.lower()

    # 500 ming
    match = re.search(r'(\d+)\s*ming', text)
    if match:
        return int(match.group(1)) * 1000

    # 20k
    match = re.search(r'(\d+)\s*k', text)
    if match:
        return int(match.group(1)) * 1000

    # oddiy raqam
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())

    return 0


def detect_category(text):
    text = text.lower()

    for category, keywords in CATEGORIES.items():
        for word in keywords:
            if word in text:
                return category, 0.9

    return "other", 0.3


def detect_person(text):
    text = text.lower()

    for word in FAMILY_WORDS:
        if word in text:
            return word

    return ""


def parse_expense(text):
    text_lower = text.lower()

    amount = extract_amount(text)

    # income yoki expense
    income_words = ["oylik", "maosh", "bonus", "daromad"]
    type_ = "expense"

    for word in income_words:
        if word in text_lower:
            type_ = "income"

    # kategoriya
    category, confidence = detect_category(text)

    # oila
    person = detect_person(text)

    if person:
        category = "family"

    # note (tozalangan)
    note = re.sub(r'\d+|\bming\b|\bk\b', '', text_lower).strip()

    return {
        "type": type_,
        "amount": amount,
        "category": category,
        "person": person,
        "note": note,
        "confidence": confidence
    }
