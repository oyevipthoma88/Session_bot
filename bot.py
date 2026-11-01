import os, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyromod import listen

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("SessionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("Pyrogram User String", callback_data="pyro_user")],
    [InlineKeyboardButton("Pyrogram Bot String", callback_data="pyro_bot")],
    [InlineKeyboardButton("Telethon String", callback_data="telethon")]
])

@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply_text(
        "**Advanced Telegram Session Generator**\n\n"
        "1. **Pyrogram User Session**\n"
        "2. **Pyrogram Bot Session**\n"
        "3. **Telethon String Session**\n\n"
        "Choose a type:",
        reply_markup=MAIN_MENU
    )

@app.on_callback_query()
async def handle_callback(_, query: CallbackQuery):
    data = query.data
    await query.message.delete()
    user_id = query.from_user.id
    try:
        if data == "pyro_bot":
            await app.send_message(user_id, "Send your **Bot Token**:")
            token = (await app.listen(user_id)).text.strip()
            try:
                bc = Client(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
                await bc.start()
                s = await bc.export_session_string()
                await bc.stop()
                await app.send_message(user_id, f"**Pyrogram Bot Session:**\n\n`{s}`")
            except Exception as e:
                await app.send_message(user_id, f"**Error:** `{e}`")
            return

        await app.send_message(user_id, "Send your **API ID**:")
        api_id = int((await app.listen(user_id)).text.strip())
        await app.send_message(user_id, "Send your **API HASH**:")
        api_hash = (await app.listen(user_id)).text.strip()
        await app.send_message(user_id, "Send your **phone** (+91...):")
        phone = (await app.listen(user_id)).text.strip()

        if data == "pyro_user":
            uc = Client(f"gen_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
            await uc.connect()
            sent = await uc.send_code(phone)
            await app.send_message(user_id, "Send the **OTP**:")
            otp = (await app.listen(user_id)).text.strip()
            try:
                await uc.sign_in(phone, sent.phone_code_hash, otp)
            except Exception as e:
                if "password" in str(e).lower():
                    await app.send_message(user_id, "2FA password:")
                    pwd = (await app.listen(user_id)).text.strip()
                    await uc.check_password(pwd)
                else:
                    raise e
            s = await uc.export_session_string()
            await app.send_message(user_id, f"**Pyrogram User Session:**\n\n`{s}`")
            try:
                await uc.send_message("me", f"**Pyrogram Session:**\n`{s}`")
            except: pass
            await uc.disconnect()

        elif data == "telethon":
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            from telethon.errors import SessionPasswordNeededError
            with TelegramClient(StringSession(), api_id, api_hash) as c:
                c.send_code_request(phone)
                await app.send_message(user_id, "Send the **OTP**:")
                otp = (await app.listen(user_id)).text.strip()
                try:
                    c.sign_in(phone, otp)
                except SessionPasswordNeededError:
                    await app.send_message(user_id, "2FA password:")
                    pwd = (await app.listen(user_id)).text.strip()
                    c.sign_in(password=pwd)
                s = c.session.save()
                await app.send_message(user_id, f"**Telethon String:**\n\n`{s}`")
                try:
                    c.send_message("me", f"**Telethon Session:**\n`{s}`")
                except: pass
    except Exception as e:
        await app.send_message(user_id, f"**Error:** `{e}`")

if __name__ == "__main__":
    logging.info("Starting Session Bot...")
    app.run()
