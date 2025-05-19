import matplotlib.pyplot as plt
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
# ----  FETCH PRICES  ─────────────────────────────────────────────
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
next_24h["hour_str"] = next_24h["dt_ee"].dt.strftime("%H:%M")

avg_30d  = past_30d["€/kWh"].mean()

# ------------------------------------------------------------------
# ──  BUILD THE VISUAL  ───────────────────────────────────
# ------------------------------------------------------------------

# Plot the next 24h prices
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(next_24h["hour_str"], next_24h["€/kWh"] * 100, marker='o')
ax.set_title("Next 24h Electricity Prices (Estonia)", fontsize=14)
ax.set_xlabel("Time")
ax.set_ylabel("Price (cents/kWh)")
ax.grid(True)

# Annotate each point with the price value
for x, y in zip(next_24h["hour_str"], next_24h["€/kWh"] * 100):
    ax.annotate(f"{y:.1f}", xy=(x, y), xytext=(0, 5),
                textcoords="offset points", ha='center', fontsize=8)

# Rotate timestamps
fig.autofmt_xdate()

# Save to PNG
img_path = "price_chart.png"
plt.savefig(img_path, bbox_inches="tight")
plt.close()

# Fetch past 120 days to compute long-term average
past_120d = fetch(now_utc - timedelta(days=120), now_utc)
avg_120d  = past_120d["€/kWh"].mean()

# ------------------------------------------------------------------
# ──  BUILD THE MESSAGE TEXT  ───────────────────────────────────
# ------------------------------------------------------------------
msg = textwrap.dedent(f"""
    ⚡ Nord Pool electricity prices |Estonia|
    • 120-day average: ({avg_120d*100:.2f} c/kWh)  
    • 30-day average: ({avg_30d*100:.2f} c/kWh)

    • Incoming 24 h:
""").strip()

for hour, price in zip(next_24h["hour_str"], next_24h["€/kWh"]):
    msg += f"\n    {hour} — {price*100:.3f} Cent/kWh"

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
# ──  SEND THE MESSAGE  ─────────────────────────────────────────
# ------------------------------------------------------------------
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
resp = requests.post(url, data=payload, timeout=30)
# Send chart image to Telegram
with open(img_path, "rb") as photo:
    files = {"photo": photo}
    data = {"chat_id": CHANNEL_ID, "caption": "📊 Price Trend for Next 24h"}
    photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    photo_resp = requests.post(photo_url, data=data, files=files, timeout=30)
    photo_resp.raise_for_status()
resp.raise_for_status()          # raises if Telegram returns an error


plt.show()                     # show the plot in a window
print(msg)