import os, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyromod import listen

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))  # optional

app = Client("SessionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ================= UI HELPERS =================
WELCOME_TEXT = (
    "╔══════════════════════════════╗\n"
    "║   🔥 **SESSION STRING GENERATOR**   ║\n"
    "╚══════════════════════════════╝\n\n"
    "╭──────────────────────────────╮\n"
    "│  ✨ **Choose your session type**  │\n"
    "╰──────────────────────────────╯\n"
)

FEATURES_TEXT = (
    "\n\n🔒 **100% Secure**  •  ⚡ **Instant**  •  💾 **Saved Messages**\n\n"
    "> 🐍 **Pyrogram** (User / Bot)\n"
    "> 📞 **Telethon** (User)\n"
    "> 🔄 **Pyrogram → Telethon** Converter\n"
    "> 🛡 **2FA Support**  •  📩 **Auto Delivery**"
)

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🐍 Pyrogram User Session", callback_data="pyro_user")],
    [InlineKeyboardButton("🤖 Pyrogram Bot Session", callback_data="pyro_bot")],
    [InlineKeyboardButton("📞 Telethon String Session", callback_data="telethon")],
    [InlineKeyboardButton("🔄 Pyrogram ➜ Telethon Converter", callback_data="convert")],
    [InlineKeyboardButton("❓ Help & About", callback_data="help")]
])

BACK_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]])

# ================= HANDLERS =================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text(
        WELCOME_TEXT + FEATURES_TEXT,
        reply_markup=MAIN_MENU,
        disable_web_page_preview=True
    )

@app.on_callback_query()
async def handle_callback(_, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    if data == "back":
        await query.message.edit_text(
            WELCOME_TEXT + FEATURES_TEXT,
            reply_markup=MAIN_MENU,
            disable_web_page_preview=True
        )
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

    # Delete old menu to avoid clutter
    try:
        await query.message.delete()
    except:
        pass

    # ---------- Pyrogram Bot ----------
    if data == "pyro_bot":
        msg = await app.send_message(user_id, "🤖 **Send your Bot Token** (from @BotFather):\n\n> Example: `123456:ABC-DEF...`")
        token_msg = await app.listen(user_id)
        token = token_msg.text.strip()
        try:
            bc = Client(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
            await bc.start()
            s = await bc.export_session_string()
            await bc.stop()
            await app.send_message(
                user_id,
                f"✅ **Pyrogram Bot Session**\n\n`{s}`\n\n"
                "> ⚠️ Keep this safe. Never share it.",
                reply_markup=BACK_BTN
            )
        except Exception as e:
            await app.send_message(user_id, f"❌ **Error:** `{e}`", reply_markup=BACK_BTN)
        return

    # ---------- Converter ----------
    if data == "convert":
        msg = await app.send_message(user_id, "🔄 **Send your Pyrogram Session String:**")
        pyro_str = (await app.listen(user_id)).text.strip()
        try:
            from pyrogram import Client as PyroClient
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            temp = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=pyro_str, in_memory=True)
            await temp.start()
            me = await temp.get_me()
            tele = TelegramClient(StringSession(), API_ID, API_HASH)
            tele.start()
            tele_str = tele.session.save()
            await temp.stop()
            await tele.disconnect()
            await app.send_message(
                user_id,
                f"✅ **Telethon String (converted)**\n\n`{tele_str}`\n\n"
                f"> 👤 Account: **{me.first_name or 'N/A'}**\n"
                "> ⚠️ Keep this safe.",
                reply_markup=BACK_BTN
            )
        except Exception as e:
            await app.send_message(user_id, f"❌ **Conversion Error:** `{e}`", reply_markup=BACK_BTN)
        return

    # ---------- User Sessions (Pyrogram / Telethon) ----------
    await app.send_message(user_id, "🆔 **Send your API ID:**")
    api_id = int((await app.listen(user_id)).text.strip())

    await app.send_message(user_id, "🔑 **Send your API HASH:**")
    api_hash = (await app.listen(user_id)).text.strip()

    await app.send_message(user_id, "📱 **Send your phone number** (with country code):\n\n> Example: `+919876543210`")
    phone = (await app.listen(user_id)).text.strip()

    if data == "pyro_user":
        uc = Client(f"gen_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
        await uc.connect()
        sent = await uc.send_code(phone)
        await app.send_message(user_id, "🔐 **Send the OTP** you received:")
        otp = (await app.listen(user_id)).text.strip()
        try:
            await uc.sign_in(phone, sent.phone_code_hash, otp)
        except Exception as e:
            if "password" in str(e).lower():
                await app.send_message(user_id, "🔒 **2FA enabled. Send your password:**")
                pwd = (await app.listen(user_id)).text.strip()
                await uc.check_password(pwd)
            else:
                raise e
        s = await uc.export_session_string()
        await app.send_message(
            user_id,
            f"✅ **Pyrogram User Session**\n\n`{s}`\n\n"
            "> 📩 Also sent to your Saved Messages.\n"
            "> ⚠️ Never share this.",
            reply_markup=BACK_BTN
        )
        try:
            await uc.send_message("me", f"🔐 **Pyrogram Session**\n`{s}`")
        except:
            pass
        await uc.disconnect()

    elif data == "telethon":
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        from telethon.errors import SessionPasswordNeededError
        with TelegramClient(StringSession(), api_id, api_hash) as c:
            c.send_code_request(phone)
            await app.send_message(user_id, "🔐 **Send the OTP** you received:")
            otp = (await app.listen(user_id)).text.strip()
            try:
                c.sign_in(phone, otp)
            except SessionPasswordNeededError:
                await app.send_message(user_id, "🔒 **2FA enabled. Send your password:**")
                pwd = (await app.listen(user_id)).text.strip()
                c.sign_in(password=pwd)
            s = c.session.save()
            await app.send_message(
                user_id,
                f"✅ **Telethon String Session**\n\n`{s}`\n\n"
                "> 📩 Also sent to your Saved Messages.\n"
                "> ⚠️ Never share this.",
                reply_markup=BACK_BTN
            )
            try:
                c.send_message("me", f"🔐 **Telethon Session**\n`{s}`")
            except:
                pass

# ================= COMMANDS =================
@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message):
    await message.reply_text(
        "❓ **Help & About**\n\n"
        "Use /start to open the menu.\n"
        "Choose a session type from the buttons.\n\n"
        "**Types:** Pyrogram User, Pyrogram Bot, Telethon, Converter.\n"
        "**Safety:** Never share your session string.",
        reply_markup=BACK_BTN
    )

if __name__ == "__main__":
    logging.info("Starting Session Bot with Advanced UI...")
    app.run()
