# Bike Finder

Automated daily tracker that monitors two sources for **Tenways e-bike** listings and sends a **Telegram notification** every evening at 10 PM.

---

## What it does

Every day at **22:00 (Amsterdam time)**, two scripts run automatically on GitHub's servers:

### 1. Amsterdam Fietsdepot checker
Scans all bikes registered at the **Amsterdam municipal bike depot** (Fietsdepot Bornhout 8) for that day. If any listing mentions "Tenways", you get a Telegram alert with the description and a direct link to the listing.

> This is useful because the depot website uses infinite scroll — you'd have to scroll through hundreds of listings manually to find a specific brand.

### 2. Marktplaats checker
Scans all **new listings posted today** on Marktplaats matching `tenways cgo600 pro`. Sends a single Telegram message with title, price, city and direct link for each result.

---

## Telegram message examples

**Fietsdepot alert:**
```
TENWAYS gevonden in Fietsdepot Amsterdam!
Datum: 22-04-2026 — 1 listing(s)

• Tenways — herenfiets (zwart)
  herenfiets electrische fiets Tenways lakschade ( zwart ).
  Locatie gevonden: Bakkersstraat, Centrum Amsterdam.
  Reg: F0363f-2500149141
  https://www.verlorenofgevonden.nl/overzicht?search=F0363f-2500149141
```

**Marktplaats alert:**
```
🛒 Tenways op Marktplaats vandaag!
📅 22-04-2026 — 3 nieuwe listing(s)

• tenways cgo600 pro | Framemaat M | Avocado groen
  € 1.399 — Haarlem
  https://www.marktplaats.nl/v/...
```

---

## Files

| File | Description |
|------|-------------|
| `check_tenways.py` | Fietsdepot Amsterdam scraper |
| `check_marktplaats.py` | Marktplaats scraper |
| `.github/workflows/check_tenways.yml` | GitHub Actions schedule (runs both scripts daily at 10 PM) |

---

## Setup

### 1. Telegram bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` — follow the prompts to get a **bot token**
3. Start a chat with your bot and send any message
4. Get your **chat ID** by opening this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
   Find the `"id"` number inside `"chat"`.

### 2. Add secrets to GitHub

Go to **Settings → Secrets → Actions** in this repo and add:

| Secret name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | your bot token |
| `TELEGRAM_CHAT_ID` | your chat ID |

### 3. Run manually

Go to **Actions → Tenways Bike Depot Check → Run workflow** to trigger immediately.

---

## Configuration

To change the Marktplaats search query, edit the top of `check_marktplaats.py`:

```python
SEARCH_QUERY = "tenways cgo600 pro"   # change to any search term
```

To change the notification time, edit `.github/workflows/check_tenways.yml`:

```yaml
- cron: '0 20 * * *'   # 20:00 UTC = 22:00 Amsterdam (CEST)
```

---

## Notes

- **No dependencies** — both scripts use only Python standard library
- GitHub automatically disables scheduled workflows after **60 days of repo inactivity**. If notifications stop, go to Actions and click "Enable workflow"
- The Marktplaats checker only reports listings with `date == "Vandaag"` (posted today), not older listings that were bumped
