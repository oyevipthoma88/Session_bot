import os
from datetime import datetime
import pytz

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
MUST_JOIN = os.environ.get("MUST_JOIN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

# Auto-join channels (comma separated, max 3)
AUTO_JOIN_CHANNELS = [
    c.strip() for c in os.environ.get("AUTO_JOIN_CHANNELS", "").split(",") if c.strip()
][:3]

# Mutable runtime state
STATE = {"maintenance": False}

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time():
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p")
