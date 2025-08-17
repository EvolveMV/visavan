#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, json, requests

APPOINTMENTS_URL = os.getenv("APPOINTMENTS_URL", "")
YATRI_SESSION    = os.getenv("YATRI_SESSION", "")          # только значение ПОСЛЕ _yatri_session=
FULL_COOKIE      = os.getenv("FULL_COOKIE", "")            # весь Cookie из DevTools (необязателен, но лучше)
X_CSRF_TOKEN     = os.getenv("X_CSRF_TOKEN", "")           # из meta[name=csrf-token] или из HAR
TG_BOT_TOKEN     = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID       = os.getenv("TG_CHAT_ID", "")
POLL_SECONDS     = int(os.getenv("POLL_SECONDS", "300"))
MODE             = os.getenv("MODE", "loop").lower()

def tg_send(msg):
    if TG_BOT_TOKEN and TG_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT_ID, "text": msg, "disable_web_page_preview": True},
                timeout=15
            )
        except Exception:
            pass

def build_headers():
    if not APPOINTMENTS_URL:
        raise RuntimeError("APPOINTMENTS_URL пуст")
    # Referer = страница назначения слотов
    referer = APPOINTMENTS_URL.split("/appointment/")[0] + "/appointment"

    # Базовый Cookie
    cookie = FULL_COOKIE.strip() if FULL_COOKIE.strip() else f"_yatri_session={YATRI_SESSION.strip()}"
    if not cookie:
        raise RuntimeError("Нет Cookie: задайте YATRI_SESSION или FULL_COOKIE")

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": referer,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie,
    }
    if X_CSRF_TOKEN:
        headers["X-CSRF-Token"] = X_CSRF_TOKEN
    return headers

def parse_days(text: str):
    # Поддержка JSON: [{"date":"YYYY-MM-DD"}, ...] или ["YYYY-MM-DD", ...]
    try:
        data = json.loads(text)
        if isinstance(data, list):
            out = []
            for item in data:
                if isinstance(item, dict) and "date" in item:
                    out.append(item["date"])
                elif isinstance(item, str):
                    out.append(item)
            return sorted(set(out))
    except Exception:
        pass
    return []

def fetch_days():
    h = build_headers()
    r = requests.get(APPOINTMENTS_URL, headers=h, timeout=30)
    if r.status_code in (401, 403):
        raise RuntimeError(f"Forbidden {r.status_code}. Проверьте YATRI_SESSION/FULL_COOKIE и X_CSRF_TOKEN/Referer.")
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    days = parse_days(r.text)
    if not days:
        # Помогаем дебажить: покажем первые 300 символов ответа
        print("[debug] Empty days, response head:", r.text[:300].replace("\n"," "))
    return days

def run_once():
    days = fetch_days()
    print("[visa-monitor] Found days:", days)
    return days

def run_loop():
    tg_send("✅ Monitor started.")
    last = set()
    while True:
        try:
            cur = set(run_once())
            new = sorted(cur - last)
            if new:
                tg_send("🎯 NEW dates: " + ", ".join(new))
            last = cur
        except Exception as e:
            msg = f"⚠️ Error: {e}"
            print(msg)
            tg_send(msg)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    if MODE == "once":
        print(run_once())
    else:
        run_loop()
