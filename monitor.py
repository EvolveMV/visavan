#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, json, requests
from urllib.parse import urlparse

# ==== ENV (заполняются в Railway → Variables) ====
APPOINTMENTS_URL = os.getenv("APPOINTMENTS_URL", "")   # пример: https://ais.usvisa-info.com/en-ca/niv/schedule/69597284/appointment/days/95.json?appointments[expedite]=false
YATRI_SESSION   = os.getenv("YATRI_SESSION", "")       # сюда вставишь ТОЛЬКО значение после _yatri_session=
TG_BOT_TOKEN    = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID      = os.getenv("TG_CHAT_ID", "")
POLL_SECONDS    = int(os.getenv("POLL_SECONDS", "300"))
MODE            = os.getenv("MODE", "loop").lower()    # loop | once
LOG_PREFIX      = "[visa-monitor]"

def tg_send(msg: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print(LOG_PREFIX, "TG not configured →", msg)
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "disable_web_page_preview": True}, timeout=15)
    except Exception as e:
        print(LOG_PREFIX, "TG send error:", e)

def build_headers():
    if not YATRI_SESSION:
        raise RuntimeError("Не задан YATRI_SESSION (Railway → Variables). Возьми значение после '_yatri_session=' и вставь.")
    referer = APPOINTMENTS_URL.split("/appointment/")[0] + "/appointment"
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": referer,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"_yatri_session={YATRI_SESSION}",
        "X-Requested-With": "XMLHttpRequest",
    }

def fetch_days():
    if not APPOINTMENTS_URL:
        raise RuntimeError("Не задан APPOINTMENTS_URL (Railway → Variables).")
    headers = build_headers()
    r = requests.get(APPOINTMENTS_URL, headers=headers, timeout=25)
    if r.status_code == 401 or r.status_code == 403:
        raise RuntimeError(f"Доступ запрещён ({r.status_code}). Проверь свежесть YATRI_SESSION.")
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    try:
        data = r.json()
    except Exception:
        # иногда приходит HTML → вытащим YYYY-MM-DD простым способом
        import re
        return sorted(set(re.findall(r"\b20\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", r.text)))
    # поддержка форматов: [{"date":"YYYY-MM-DD"}, ...] или ["YYYY-MM-DD", ...]
    days = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "date" in item:
                days.append(item["date"])
            elif isinstance(item, str):
                days.append(item)
    return sorted(set(days))

def run_once():
    days = fetch_days()
    print(LOG_PREFIX, "Found days:", days)
    return days

def run_loop():
    tg_send("✅ Vancouver visa slot monitor started.")
    last = set()
    while True:
        try:
            current = set(run_once())
            new = sorted(current - last)
            if new:
                tg_send("🎯 NEW Vancouver dates: " + ", ".join(new))
            last = current
        except Exception as e:
            err = f"⚠️ Monitor error: {e}"
            print(LOG_PREFIX, err)
            tg_send(err)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    if MODE == "once":
        print(run_once())
    else:
        run_loop()
