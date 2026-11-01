from pyrogram import filters
from .client import app
from .config import OWNER_ID, STATE, AUTO_JOIN_CHANNELS

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == OWNER_ID

OWNER_FILTER = filters.create(owner_only)

@app.on_message(filters.command("ping") & OWNER_FILTER)
async def ping(_, message):
    await message.reply_text("🏓 **Pong!** Bot alive.")

@app.on_message(filters.command("stats") & OWNER_FILTER)
async def stats(_, message):
    await message.reply_text(
        f"📊 **Bot Stats**\n\n"
        f"Status: Running\n"
        f"Maintenance: **{STATE['maintenance']}**\n"
        f"Auto-Join Channels: `{len(AUTO_JOIN_CHANNELS)}`"
    )

@app.on_message(filters.command("maintenance") & OWNER_FILTER)
async def maint(_, message):
    STATE["maintenance"] = not STATE["maintenance"]
    await message.reply_text(f"🔧 Maintenance: **{'ON' if STATE['maintenance'] else 'OFF'}**")
