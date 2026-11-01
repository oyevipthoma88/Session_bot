import os
import pyromod  # noqa: F401 — MUST import before Client
from pyrogram import Client
from pyrogram.enums import ParseMode

app = Client(
    "SessionBot",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", ""),
    in_memory=True,
    parse_mode=ParseMode.HTML,
    plugins=dict(root="plugins", exclude=["client"])
)
