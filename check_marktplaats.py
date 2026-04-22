#!/usr/bin/env python3
"""
Tenways Marktplaats Checker
---------------------------
Fetches today's Tenways listings from Marktplaats and sends a
Telegram alert with each new listing.

No third-party dependencies — uses only Python standard library.

Usage:
    python3 check_marktplaats.py

Environment variables (required for Telegram):
    TELEGRAM_BOT_TOKEN   - your bot token from @BotFather
    TELEGRAM_CHAT_ID     - your personal chat ID
"""

import gzip
import json
import os
import time
import urllib.request
import urllib.parse

# ── Configuration ──────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

SEARCH_QUERY = "tenways cgo600 pro"   # change to "tenways" for all models
PAGE_SIZE    = 100

# ───────────────────────────────────────────────────────────────────────────────

API_BASE = "https://www.marktplaats.nl/lrp/api/search"


def fetch_page(offset: int) -> dict:
    params = {
        "query":      SEARCH_QUERY,
        "limit":      PAGE_SIZE,
        "offset":     offset,
        "sortBy":     "SORT_INDEX",
        "sortOrder":  "DECREASING",
        "dateRange":  "TODAY",
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent":      "Mozilla/5.0",
            "Accept":          "application/json",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw.decode())


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] BOT_TOKEN or CHAT_ID not set — skipping notification.")
        print("[Telegram] Message that would have been sent:")
        print(message)
        return
    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     message,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("[Telegram] Notification sent.")
            else:
                print(f"[Telegram] Unexpected status: {resp.status}")
    except Exception as e:
        print(f"[Telegram] Failed to send: {e}")


def format_listing(listing: dict) -> str:
    title     = listing.get("title", "?")
    desc      = (listing.get("description", "") or "").strip()
    price_info = listing.get("priceInfo", {})
    price_cents = price_info.get("priceCents")
    price_type  = price_info.get("priceType", "")
    location  = listing.get("location", {})
    city      = location.get("cityName", "") or ""
    vip_url   = "https://www.marktplaats.nl" + listing.get("vipUrl", "")

    # Format price
    if price_cents:
        price_str = f"€ {price_cents / 100:,.0f}".replace(",", ".")
    elif price_type == "SEE_DESCRIPTION":
        price_str = "Zie omschrijving"
    elif price_type == "ON_REQUEST":
        price_str = "Op aanvraag"
    elif price_type == "MIN_BID":
        price_str = f"Bieden vanaf € {price_cents / 100:,.0f}".replace(",", ".") if price_cents else "Bieden"
    elif price_type == "FREE":
        price_str = "Gratis"
    else:
        price_str = "?"

    if len(desc) > 120:
        desc = desc[:120].rstrip() + "..."

    return (
        f"• <b>{title}</b>\n"
        f"  {price_str} — {city}\n"
        f"  {desc}\n"
        f"  <a href=\"{vip_url}\">{vip_url}</a>"
    )


def main():
    from datetime import date
    today = date.today().strftime("%d-%m-%Y")
    print(f"Checking Marktplaats listings for '{SEARCH_QUERY}' today ({today})...")

    offset   = 0
    total    = None
    listings = []

    while True:
        data      = fetch_page(offset)
        page      = data.get("listings", [])

        if total is None:
            total = data.get("totalResultCount", 0)
            print(f"Total listings today: {total}")
            if total == 0:
                print("No listings found today.")
                break

        if not page:
            break

        listings.extend(l for l in page if l.get("date") == "Vandaag")
        offset += len(page)
        print(f"  Fetched {min(offset, total)}/{total}...", end="\r")

        if offset >= total:
            break

        time.sleep(0.3)

    print(f"\nDone. Found {len(listings)} new listing(s) posted today.")

    if listings:
        header = (
            f"🛒 <b>Tenways op Marktplaats vandaag!</b>\n"
            f"📅 {today} — {len(listings)} nieuwe listing(s)\n\n"
        )
        body    = "\n\n".join(format_listing(l) for l in listings)
        message = header + body

        # Telegram has a 4096 char limit — split into chunks if needed
        MAX = 4000
        if len(message) <= MAX:
            print("\n" + message)
            send_telegram(message)
        else:
            chunks = []
            current = header
            for l in listings:
                block = format_listing(l) + "\n\n"
                if len(current) + len(block) > MAX:
                    chunks.append(current.rstrip())
                    current = block
                else:
                    current += block
            if current.strip():
                chunks.append(current.rstrip())

            print(f"Message split into {len(chunks)} part(s).")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n--- Part {i} ---\n{chunk}")
                send_telegram(chunk)
                time.sleep(1)
    else:
        print(f"No listings found today. No notification sent.")


if __name__ == "__main__":
    main()
