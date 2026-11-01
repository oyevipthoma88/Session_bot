from pyrogram import filters
from .client import app
from .config import OWNER_ID, STATE, AUTO_JOIN_CHANNELS
from .database import set_start_pic, clear_start_pic, get_stats, is_enabled

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == OWNER_ID

OWNER_FILTER = filters.create(owner_only)

@app.on_message(filters.command("ping") & OWNER_FILTER)
async def ping(_, message):
    await message.reply_text("🏓 **Pong!** Bot alive.")

@app.on_message(filters.command("stats") & OWNER_FILTER)
async def stats_cmd(_, message):
    if not is_enabled():
        await message.reply_text("⚠️ MongoDB not configured. Set `MONGO_URI`.")
        return
    s = await get_stats()
    await message.reply_text(
        f"📊 **Bot Stats**\n\n"
        f"👥 Total Users: **{s.get('users', 0)}**\n"
        f"🔐 Total Sessions: **{s.get('sessions', 0)}**\n"
        f"📅 Today's Sessions: **{s.get('today', 0)}**\n\n"
        f"Status: Running\n"
        f"Maintenance: **{STATE['maintenance']}**\n"
        f"Auto-Join Channels: `{len(AUTO_JOIN_CHANNELS)}`"
    )

@app.on_message(filters.command("maintenance") & OWNER_FILTER)
async def maint(_, message):
    STATE["maintenance"] = not STATE["maintenance"]
    await message.reply_text(f"🔧 Maintenance: **{'ON' if STATE['maintenance'] else 'OFF'}**")

@app.on_message(filters.command("setpic") & OWNER_FILTER)
async def setpic(_, message):
    if not is_enabled():
        await message.reply_text("⚠️ MongoDB not configured.")
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("📸 Kisi photo ko **reply** karke `/setpic` bhejein.")
        return
    file_id = message.reply_to_message.photo.file_id
    ok = await set_start_pic(file_id)
    if ok:
        await message.reply_text("✅ **Start picture MongoDB me save ho gayi!** (permanent)")
    else:
        await message.reply_text("❌ Save failed. Logs check karein.")

@app.on_message(filters.command("clearpic") & OWNER_FILTER)
async def clearpic(_, message):
    ok = await clear_start_pic()
    await message.reply_text("✅ Start picture removed." if ok else "❌ Failed.")
