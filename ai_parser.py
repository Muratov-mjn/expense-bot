from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime, timedelta

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def normalize_numbers(text):
    text = (text or "").lower()

    text = re.sub(r'(\d+)\s*k\b', lambda m: str(int(m.group(1)) * 1000), text)
    text = re.sub(r'(\d+)\s*ming\b',
                  lambda m: str(int(m.group(1)) * 1000), text)
    text = re.sub(r'(\d+)\s*mln\b',
                  lambda m: str(int(m.group(1)) * 1000000), text)
    text = re.sub(r'(\d+)\s*million\b',
                  lambda m: str(int(m.group(1)) * 1000000), text)

    return text


def safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        pass

    match_array = re.search(r'\[.*\]', text, re.S)
    if match_array:
        try:
            return json.loads(match_array.group())
        except Exception:
            pass

    match_object = re.search(r'\{.*\}', text, re.S)
    if match_object:
        try:
            return json.loads(match_object.group())
        except Exception:
            pass

    return None


def extract_relative_date(text, today_str):
    low = (text or "").lower()

    try:
        base_date = datetime.strptime(today_str, "%Y-%m-%d").date()
    except Exception:
        base_date = datetime.now().date()

    if "bugun" in low:
        return base_date.strftime("%Y-%m-%d")

    if "kecha" in low:
        return (base_date - timedelta(days=1)).strftime("%Y-%m-%d")

    if "ertaga" in low:
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")

    match_days = re.search(r'(\d+)\s*kun\s*oldin', low)
    if match_days:
        days = int(match_days.group(1))
        return (base_date - timedelta(days=days)).strftime("%Y-%m-%d")

    if "bir hafta oldin" in low:
        return (base_date - timedelta(days=7)).strftime("%Y-%m-%d")

    match_weeks = re.search(r'(\d+)\s*hafta\s*oldin', low)
    if match_weeks:
        weeks = int(match_weeks.group(1))
        return (base_date - timedelta(days=weeks * 7)).strftime("%Y-%m-%d")

    return base_date.strftime("%Y-%m-%d")


def normalize_item(item, original_text, today_str):
    if not isinstance(item, dict):
        return None

    try:
        amount = int(float(item.get("amount", 0)))
    except Exception:
        amount = 0

    type_ = str(item.get("type", "expense")).strip().lower()
    if type_ not in ["expense", "income"]:
        type_ = "expense"

    category = str(item.get("category", "Boshqa")).strip() or "Boshqa"
    note = str(item.get("note", original_text)).strip() or original_text
    date = str(item.get("date", "")).strip()

    if not date:
        date = extract_relative_date(note, today_str)

    return {
        "amount": amount,
        "type": type_,
        "category": category,
        "note": note,
        "date": date
    }


def fallback_parse(text, today_str):
    parts = [p.strip() for p in text.split(",") if p.strip()]
    results = []

    for part in parts:
        match = re.search(r'(\d+)', part)
        if not match:
            continue

        amount = int(match.group(1))
        low = part.lower()

        if any(word in low for word in ["taksi", "taxi", "benzin", "gaz", "yoqilg", "mashina", "moshina"]):
            category = "Transport"
        elif any(word in low for word in ["ovqat", "tushlik", "non", "market", "bozor", "ro'zg'or", "oziq", "shirinlik"]):
            category = "Ovqat"
        else:
            category = "Boshqa"

        results.append({
            "amount": amount,
            "type": "expense",
            "category": category,
            "note": part,
            "date": extract_relative_date(part, today_str)
        })

    return results


def parse_with_ai(text, today):
    text = normalize_numbers(text)

    prompt = f"""
Extract financial transactions from this message:

{text}

Today's date is: {today}

Return ONLY valid JSON array.

Each item must look like:
[
  {{
    "amount": number,
    "type": "expense or income",
    "category": "Ovqat / Transport / Uy / Kommunal / Sog'liq / O'yin-kulgi / Daromad / Boshqa",
    "note": "short description",
    "date": "YYYY-MM-DD"
  }}
]

Rules:
- Return JSON array only
- type must be expense or income
- amount must be number
- detect relative dates using today's date = {today}
- bugun = {today}
- kecha = today's date - 1 day
- 2 kun oldin = today's date - 2 days
- bir hafta oldin = today's date - 7 days
- if date is not mentioned, use {today}
- Do not write explanations
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial transaction parser. Return JSON array only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = response.choices[0].message.content.strip()
        data = safe_json_parse(result)

        if not data:
            return fallback_parse(text, today)

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return fallback_parse(text, today)

        cleaned = []
        for item in data:
            normalized = normalize_item(item, text, today)
            if normalized and normalized["amount"] > 0:
                cleaned.append(normalized)

        if cleaned:
            return cleaned

        return fallback_parse(text, today)

    except Exception:
        return fallback_parse(text, today)
