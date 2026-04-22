#!/usr/bin/env python3
"""
Tenways Bike Depot Checker
--------------------------
Scrapes the Amsterdam Fietsdepot listings for today via the
verlorenofgevonden.nl API and sends a Telegram alert if any
listing mentions "tenways".

No third-party dependencies — uses only Python standard library.

Usage:
    python3 check_tenways.py

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
from datetime import date

# ── Configuration ──────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Keywords to search for (all case-insensitive, any match triggers alert)
KEYWORDS = ["tenways", "ten ways", "tenway"]

# How many results to fetch per API call (higher = fewer calls)
PAGE_SIZE = 100

# ───────────────────────────────────────────────────────────────────────────────

API_BASE = "https://verlorenofgevonden.nl/scripts/ez.php"


def fetch_page(date_str: str, offset: int) -> dict:
    params = {
        "q":         "fietsendepot amsterdam",
        "org":       "",
        "date_from": date_str,
        "date_to":   date_str,
        "from":      str(offset),
        "size":      str(PAGE_SIZE),
        "site":      "nl",
        "timestamp": str(int(time.time() * 1000)),
    }
    url  = API_BASE + "?" + urllib.parse.urlencode(params)
    body = json.dumps({"subcategories": [], "colors": [], "cities": []}).encode()
    req  = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type":     "application/json",
            "Accept-Encoding":  "gzip",
            "X-Requested-With": "XMLHttpRequest",
            "Referer":          "https://www.verlorenofgevonden.nl/overzicht?search=fietsendepot+amsterdam",
            "User-Agent":       "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw.decode())


def listing_matches(source: dict) -> bool:
    """Return True if any keyword appears in the listing's searchable fields."""
    text = " ".join([
        source.get("Brand", "") or "",
        source.get("Description", "") or "",
        source.get("SubCategory", "") or "",
    ]).lower()
    return any(kw.lower() in text for kw in KEYWORDS)


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] BOT_TOKEN or CHAT_ID not set — skipping notification.")
        print("[Telegram] Message that would have been sent:")
        print(message)
        return
    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "HTML",
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


def format_match(source: dict) -> str:
    brand   = source.get("Brand", "onbekend") or "onbekend"
    subcat  = source.get("SubCategory", "") or ""
    color   = source.get("Color", "") or ""
    desc    = (source.get("Description", "") or "").strip()
    reg_num = source.get("ObjectNumber", "") or ""
    link    = f"https://www.verlorenofgevonden.nl/overzicht?search={urllib.parse.quote(reg_num)}"

    if len(desc) > 150:
        desc = desc[:150].rstrip() + "..."

    return (
        f"• {brand} — {subcat} ({color})\n"
        f"  {desc}\n"
        f"  Reg: {reg_num}\n"
        f"  {link}"
    )


def main():
    today    = date.today()
    date_str = today.strftime("%d-%m-%Y")
    print(f"Checking Fietsdepot Amsterdam listings for {date_str} (today)...")

    offset  = 0
    total   = None
    matches = []

    while True:
        data      = fetch_page(date_str, offset)
        hits      = data.get("hits", {})

        if total is None:
            total = hits.get("total", 0)
            print(f"Total listings for {date_str}: {total}")
            if total == 0:
                print("No listings found.")
                break

        page_hits = hits.get("hits", [])
        if not page_hits:
            break

        for hit in page_hits:
            source = hit.get("_source", {})
            if listing_matches(source):
                matches.append(source)

        offset += len(page_hits)
        print(f"  Scanned {min(offset, total)}/{total}...", end="\r")

        if offset >= total:
            break

        time.sleep(0.3)  # be polite to the server

    print(f"\nDone. Checked {total} listings — found {len(matches)} match(es).")

    if matches:
        header = (
            f"TENWAYS gevonden in Fietsdepot Amsterdam!\n"
            f"Datum: {date_str} — {len(matches)} listing(s)\n\n"
        )
        body    = "\n\n".join(format_match(m) for m in matches)
        message = header + body
        print("\n" + message)
        send_telegram(message)
    else:
        print(f"No Tenways found for {date_str}. No notification sent.")


if __name__ == "__main__":
    main()
