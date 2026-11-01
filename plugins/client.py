import os
from pyrogram import Client
from pyrogram.enums import ParseMode

# Smart Plugins DISABLED — manual import in bot.py handles registration
app = Client(
    "SessionBot",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", ""),
    in_memory=True,
    parse_mode=ParseMode.HTML
)
