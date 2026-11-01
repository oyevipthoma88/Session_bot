from pyrogram import filters
from pyrogram.enums import ParseMode
from .client import app
from .config import OWNER_ID, STATE, AUTO_JOIN_CHANNELS, LOG_CHANNEL_ID
from .database import set_start_pic, clear_start_pic, get_stats, is_enabled

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == OWNER_ID

OWNER_FILTER = filters.create(owner_only)

@app.on_message(filters.command("ping") & OWNER_FILTER)
async def ping(_, message):
    await message.reply_text("🏓 <b>Pong!</b>", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("stats") & OWNER_FILTER)
async def stats_cmd(_, message):
    if not is_enabled():
        await message.reply_text("⚠️ <b>MongoDB not configured.</b>", parse_mode=ParseMode.HTML)
        return
    s = await get_stats()
    txt = (
        "<b>📊 Bot Stats</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Total Users:</b> {s.get('users', 0)}\n"
        f"🔐 <b>Total Sessions:</b> {s.get('sessions', 0)}\n"
        f"📅 <b>Today:</b> {s.get('today', 0)}\n\n"
        f"⚙️ <b>Maintenance:</b> {'🔧 ON' if STATE['maintenance'] else '✅ OFF'}\n"
        f"📢 <b>Auto-Join:</b> {len(AUTO_JOIN_CHANNELS)} channels"
    )
    await message.reply_text(txt, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("maintenance") & OWNER_FILTER)
async def maint(_, message):
    STATE["maintenance"] = not STATE["maintenance"]
    await message.reply_text(
        f"🔧 <b>Maintenance:</b> {'ON' if STATE['maintenance'] else 'OFF'}",
        parse_mode=ParseMode.HTML)

@app.on_message(filters.command("setpic") & OWNER_FILTER)
async def setpic(_, message):
    if not is_enabled():
        await message.reply_text("⚠️ MongoDB not configured.", parse_mode=ParseMode.HTML)
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("📸 <b>Photo ko reply karke /setpic bhejein.</b>",
                                 parse_mode=ParseMode.HTML)
        return
    file_id = message.reply_to_message.photo.file_id
    ok = await set_start_pic(file_id)
    await message.reply_text(
        "✅ <b>Start picture saved permanently!</b>" if ok else "❌ Save failed.",
        parse_mode=ParseMode.HTML)

@app.on_message(filters.command("clearpic") & OWNER_FILTER)
async def clearpic(_, message):
    ok = await clear_start_pic()
    await message.reply_text("✅ Removed." if ok else "❌ Failed.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("testlog") & OWNER_FILTER)
async def testlog(_, message):
    lines = ["<b>🔍 LOG DIAGNOSTICS</b>", "━━━━━━━━━━━━━━━━━━━━━", ""]
    lines.append("<b>Config</b>")
    lines.append(f"├ OWNER_ID: <code>{OWNER_ID or 'NOT SET'}</code>")
    lines.append(f"└ LOG_CHANNEL_ID: <code>{LOG_CHANNEL_ID or 'NOT SET'}</code>")
    lines.append("")

    if OWNER_ID:
        try:
            await app.send_message(OWNER_ID, "✅ <b>Owner DM test OK</b>", parse_mode=ParseMode.HTML)
            lines.append("✅ <b>Owner DM:</b> Working")
        except Exception as e:
            lines.append(f"❌ <b>Owner DM:</b> <code>{type(e).__name__}: {str(e)[:80]}</code>")
    else:
        lines.append("⚠️ <b>Owner DM:</b> OWNER_ID not set")

    if LOG_CHANNEL_ID:
        try:
            await app.send_message(LOG_CHANNEL_ID, "✅ <b>Log Channel test OK</b>",
                                   parse_mode=ParseMode.HTML)
            lines.append("✅ <b>Log Channel:</b> Working")
        except Exception as e:
            lines.append(f"❌ <b>Log Channel:</b> <code>{type(e).__name__}: {str(e)[:80]}</code>")
            lines.append("💡 <i>Bot ko channel me admin banayein aur ID check karein (-100 se shuru)</i>")
    else:
        lines.append("⚠️ <b>Log Channel:</b> LOG_CHANNEL_ID not set")

    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

@app.on_message(filters.command("logs") & OWNER_FILTER)
async def logs_help(_, message):
    await message.reply_text(
        "<b>📝 Logging Commands</b>\n\n"
        "/testlog — Diagnose log setup\n"
        "/stats — Bot statistics\n"
        "/maintenance — Toggle\n"
        "/setpic — Reply photo to set start pic\n"
        "/clearpic — Remove start pic",
        parse_mode=ParseMode.HTML)
