import os
from datetime import datetime
import pytz

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
def _normalize_must_join(raw):
    if not raw:
        return ""
    raw = raw.strip()
    try:
        return int(raw)
    except ValueError:
        pass
    for prefix in ("https://t.me/", "http://t.me/", "t.me/", "https://telegram.me/", "telegram.me/"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    if raw.startswith("@"):
        raw = raw[1:]
    return raw  # Pyrogram accepts bare username

MUST_JOIN = _normalize_must_join(os.environ.get("MUST_JOIN", ""))
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
