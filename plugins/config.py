import os
from datetime import datetime
import pytz

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
MUST_JOIN = os.environ.get("MUST_JOIN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

def _parse_chat(key):
    raw = os.environ.get(key, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return raw

LOG_CHANNEL_ID = _parse_chat("LOG_CHANNEL_ID")
MONGO_URI = os.environ.get("MONGO_URI", "").strip()
START_PIC = os.environ.get("START_PIC", "").strip()

AUTO_JOIN_CHANNELS = [
    c.strip() for c in os.environ.get("AUTO_JOIN_CHANNELS", "").split(",") if c.strip()
][:3]

STATE = {"maintenance": False}
IST = pytz.timezone("Asia/Kolkata")

def get_ist_time():
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p")

# ---- Links (optional) ----
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "").strip()   # e.g. https://t.me/YourUpdates or @YourUpdates
SUPPORT_GROUP = os.environ.get("SUPPORT_GROUP", "").strip()     # e.g. https://t.me/YourSupport or @YourSupport

def _normalize_link(link):
    if not link:
        return ""
    if link.startswith("http://") or link.startswith("https://"):
        return link
    if link.startswith("@"):
        return f"https://t.me/{link[1:]}"
    return f"https://t.me/{link}"
