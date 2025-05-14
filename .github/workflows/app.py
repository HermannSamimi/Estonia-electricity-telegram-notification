import os
import requests
import textwrap
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo     # std-lib ≥3.9

load_dotenv()                # loads .env file into os.environ

# ------------------------------------------------------------------
# TELEGRAM CREDENTIALS  (store them safely!)
# ------------------------------------------------------------------
TOKEN      = os.getenv("TG_BOT_TOKEN")        # or paste the string
CHANNEL_ID = os.getenv("TG_CHANNEL_ID")       # "@mychannel"  or  "-1001234567890"

# ------------------------------------------------------------------
# 1)  ──  FETCH PRICES  ─────────────────────────────────────────────
# (same logic you already have; shortened here for clarity)
# ------------------------------------------------------------------
EE_TZ  = ZoneInfo("Europe/Tallinn")
API    = "https://dashboard.elering.ee/api/nps/price"
ISO    = "%Y-%m-%dT%H:%M:%S.000Z"

def fetch(start, end):
    params = {"start": start.strftime(ISO), "end": end.strftime(ISO)}
    data   = requests.get(API, params=params, timeout=30).json()["data"]["ee"]
    df     = pd.DataFrame(data)
    df["dt_utc"]  = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df["dt_ee"]   = df["dt_utc"].dt.tz_convert(EE_TZ)
    df["€/kWh"]   = df["price"]/1000
    return df[["dt_ee", "€/kWh"]].sort_values("dt_ee")

now_ee   = datetime.now(EE_TZ).replace(minute=0, second=0, microsecond=0)
now_utc  = now_ee.astimezone(timezone.utc)

past_30d = fetch(now_utc - timedelta(days=30), now_utc)
next_24h = fetch(now_utc, now_utc + timedelta(hours=24))

avg_30d  = past_30d["€/kWh"].mean()

# ------------------------------------------------------------------
# 2)  ──  BUILD THE MESSAGE TEXT  ───────────────────────────────────
# ------------------------------------------------------------------
msg = textwrap.dedent(f"""
    ⚡ *Nord Pool spot prices* (Estonia)

    • 30-day average: *{avg_30d:.3f} €/kWh* ({avg_30d*100:.1f} c/kWh)

    • Incoming 24 h:
""").strip()

for ts, price in next_24h.itertuples(index=False):
    msg += f"\n    {ts:%d %b %H:%M} — {price:.3f} €/kWh"

# Telegram MarkdownV2 needs special characters escaped (`_`, `-`, `.`, etc.).
def escape_md(text: str) -> str:
    specials = r"_*[]()~`>#+-=|{}.!"  # official list from Bot API docs
    return "".join("\\"+c if c in specials else c for c in text)

payload = {
    "chat_id": CHANNEL_ID,
    "text":    escape_md(msg),
    "parse_mode": "MarkdownV2",
    "disable_web_page_preview": True,
}

# ------------------------------------------------------------------
# 3)  ──  SEND THE MESSAGE  ─────────────────────────────────────────
# ------------------------------------------------------------------
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
resp = requests.post(url, data=payload, timeout=30)
resp.raise_for_status()          # raises if Telegram returns an error

print("✅ Sent to Telegram")