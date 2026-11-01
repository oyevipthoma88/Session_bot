from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .client import app
from .config import OWNER_ID, STATE, AUTO_JOIN_CHANNELS, LOG_CHANNEL_ID
from .database import set_start_pic, clear_start_pic, get_stats, is_enabled, get_all_users

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == OWNER_ID

OWNER_FILTER = filters.create(owner_only)

OWNER_PANEL = InlineKeyboardMarkup([
    [InlineKeyboardButton("🖼  Set Start Pic", callback_data="owner_setpic")],
    [InlineKeyboardButton("📢  Broadcast", callback_data="owner_broadcast")],
    [InlineKeyboardButton("📊  Stats", callback_data="owner_stats")],
    [InlineKeyboardButton("🔧  Maintenance", callback_data="owner_maint")],
    [InlineKeyboardButton("🧪  Test Log", callback_data="owner_testlog")],
])

@app.on_message(filters.command("start") & filters.private & OWNER_FILTER)
async def owner_start(_, message):
    await message.reply_text(
        "<b>👑 OWNER PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome back, Owner!\n"
        "Yahan se bot manage karein.",
        reply_markup=OWNER_PANEL,
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^owner_"))
async def owner_callbacks(_, query):
    data = query.data
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.answer("❌ Owner only!", show_alert=True)
        return

    await query.answer()

    if data == "owner_stats":
        if not is_enabled():
            await query.message.edit_text("⚠️ MongoDB not configured.", reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML)
            return
        s = await get_stats()
        await query.message.edit_text(
            "<b>📊 Bot Stats</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Total Users:</b> {s.get('users', 0)}\n"
            f"🔐 <b>Total Sessions:</b> {s.get('sessions', 0)}\n"
            f"📅 <b>Today:</b> {s.get('today', 0)}\n\n"
            f"⚙️ <b>Maintenance:</b> {'🔧 ON' if STATE['maintenance'] else '✅ OFF'}\n"
            f"📢 <b>Auto-Join:</b> {len(AUTO_JOIN_CHANNELS)} channels",
            reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML
        )

    elif data == "owner_maint":
        STATE["maintenance"] = not STATE["maintenance"]
        await query.message.edit_text(
            f"🔧 <b>Maintenance:</b> {'ON' if STATE['maintenance'] else 'OFF'}",
            reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML
        )

    elif data == "owner_testlog":
        lines = ["<b>🔍 LOG DIAGNOSTICS</b>", "━━━━━━━━━━━━━━━━━━━━━", ""]
        lines.append(f"├ OWNER_ID: <code>{OWNER_ID or 'NOT SET'}</code>")
        lines.append(f"└ LOG_CHANNEL_ID: <code>{LOG_CHANNEL_ID or 'NOT SET'}</code>")
        lines.append("")
        if OWNER_ID:
            try:
                await app.send_message(OWNER_ID, "✅ <b>Owner DM test OK</b>", parse_mode=ParseMode.HTML)
                lines.append("✅ <b>Owner DM:</b> Working")
            except Exception as e:
                lines.append(f"❌ <b>Owner DM:</b> <code>{type(e).__name__}: {str(e)[:80]}</code>")
        if LOG_CHANNEL_ID:
            try:
                await app.send_message(LOG_CHANNEL_ID, "✅ <b>Log Channel test OK</b>", parse_mode=ParseMode.HTML)
                lines.append("✅ <b>Log Channel:</b> Working")
            except Exception as e:
                lines.append(f"❌ <b>Log Channel:</b> <code>{type(e).__name__}: {str(e)[:80]}</code>")
                lines.append("💡 <i>Bot ko channel me admin banayein aur ID check karein (-100 se shuru)</i>")
        else:
            lines.append("⚠️ <b>Log Channel:</b> LOG_CHANNEL_ID not set")
        await query.message.edit_text("\n".join(lines), reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML)

    elif data == "owner_setpic":
        await query.message.edit_text(
            "🖼 <b>Set Start Pic</b>\n\nKisi photo ko reply karke <code>/setpic</code> bhejein.",
            reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML
        )

    elif data == "owner_broadcast":
        await query.message.edit_text(
            "📢 <b>Broadcast</b>\n\n"
            "Jis message ko broadcast karna hai usko <b>reply</b> karke <code>/broadcast</code> bhejein.",
            reply_markup=OWNER_PANEL, parse_mode=ParseMode.HTML
        )

@app.on_message(filters.command("setpic") & OWNER_FILTER)
async def setpic(_, message):
    if not is_enabled():
        await message.reply_text("⚠️ MongoDB not configured.", parse_mode=ParseMode.HTML)
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("📸 <b>Photo ko reply karke /setpic bhejein.</b>", parse_mode=ParseMode.HTML)
        return
    file_id = message.reply_to_message.photo.file_id
    ok = await set_start_pic(file_id)
    await message.reply_text(
        "✅ <b>Start picture saved permanently!</b>" if ok else "❌ Save failed.",
        parse_mode=ParseMode.HTML
    )

@app.on_message(filters.command("clearpic") & OWNER_FILTER)
async def clearpic(_, message):
    ok = await clear_start_pic()
    await message.reply_text("✅ Removed." if ok else "❌ Failed.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("broadcast") & OWNER_FILTER)
async def broadcast_cmd(_, message):
    if not message.reply_to_message:
        await message.reply_text("📢 <b>Kisi message ko reply karke /broadcast bhejein.</b>", parse_mode=ParseMode.HTML)
        return
    users = await get_all_users()
    if not users:
        await message.reply_text("⚠️ No users found.", parse_mode=ParseMode.HTML)
        return
    sent, failed = 0, 0
    status = await message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    for uid in users:
        try:
            await message.reply_to_message.copy(uid)
            sent += 1
        except Exception:
            failed += 1
    await status.edit_text(
        f"📢 <b>Broadcast Done</b>\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode=ParseMode.HTML
    )
