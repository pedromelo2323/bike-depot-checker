# Tenways Bike Depot Checker

Automatically scrapes the Amsterdam Fietsdepot listings daily and sends a **Telegram alert** if any listing mentions **Tenways**.

---

## How it works

The script calls the hidden JSON API behind [verlorenofgevonden.nl](https://www.verlorenofgevonden.nl/overzicht?search=fietsendepot+amsterdam), fetching **all of today's listings** in one go (no infinite scrolling). It then searches every listing's brand, description and category for the word "tenways" and notifies you via Telegram if found.

---

## Setup

### 1. Install Python dependency

```bash
pip3 install requests
```

### 2. Create a Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts — you'll get a **bot token** like `123456:ABCdef...`
3. Start a chat with your new bot (search its username and press Start)
4. Get your **chat ID** by visiting this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
   Send a message to your bot first, then open that URL — look for `"id"` inside `"chat"`.

### 3. Set your credentials

Add these two lines to your shell profile (`~/.zshrc`):

```bash
export TELEGRAM_BOT_TOKEN="123456:ABCdef..."
export TELEGRAM_CHAT_ID="987654321"
```

Then reload:

```bash
source ~/.zshrc
```

### 4. Test it manually

```bash
cd "/Users/pedro.melo/Desktop/Project Bike Deposit"
python3 check_tenways.py
```

You should see output like:
```
Checking Fietsdepot Amsterdam listings for 22-04-2026...
Total listings today: 329
  Scanned 329/329...
Done. Checked 329 listings — found 0 match(es).
No Tenways found for today (22-04-2026). No notification sent.
```

---

## Schedule it daily with cron

Run this to open your crontab:

```bash
crontab -e
```

Add this line to run the script every day at **19:00 (7 PM)**, scanning the previous day's listings:

```
0 19 * * * TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" /usr/bin/python3 "/Users/pedro.melo/Desktop/Project Bike Deposit/check_tenways.py" >> "/Users/pedro.melo/Desktop/Project Bike Deposit/check_tenways.log" 2>&1
```

> **Note:** Replace the token and chat ID with your actual values. The `>>` part saves a log file so you can check past runs.

To verify the cron job was added:
```bash
crontab -l
```

---

## What triggers an alert?

The script searches for these keywords (case-insensitive) in each listing's brand, description and category:
- `tenways`
- `ten ways`
- `tenway`

When found, you receive a Telegram message like:

> 🚲 **TENWAYS gevonden in Fietsdepot Amsterdam!**
> 📅 22-04-2026 — 1 listing(s)
>
> • **Tenways** — e-bike (zwart)
>   e-bike Tenways ( zwart ). Locatie gevonden: ...
>   Registratienummer: `F0363f-250012345`
>   [Bekijk listing](https://formulieren.verlorenofgevonden.nl/...)

---

## Files

| File | Description |
|------|-------------|
| `check_tenways.py` | Main script |
| `check_tenways.log` | Auto-created log of past runs (after cron runs) |
