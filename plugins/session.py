from pyrogram import filters
from pyrogram.enums import ParseMode
from .client import app
from .helpers import (
    CANCEL_BTN, PROMPT_BOT_TOKEN, PROMPT_PYRO_STRING, PROMPT_PHONE,
    trace, force_sub_check, handle_error,
)
from .state import set_state, clear_state

@app.on_callback_query(filters.regex(r"^(pyro_user|pyro_bot|telethon|convert)$"))
async def session_cb(_, query):
    await query.answer("⏳ Starting...")
    uid = query.from_user.id
    data = query.data
    try:
        if not await force_sub_check(query.message):
            return
        old = clear_state(uid)
        if old and old["data"].get("client"):
            try:
                await old["data"]["client"].disconnect()
            except Exception:
                pass
        await trace(query.from_user, "BUTTON", button=data)
        try:
            await query.message.delete()
        except Exception:
            pass
        if data == "pyro_bot":
            set_state(uid, "bot_token", type="pyro_bot")
            await app.send_message(uid, PROMPT_BOT_TOKEN, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
        elif data == "convert":
            set_state(uid, "pyro_string", type="convert")
            await app.send_message(uid, PROMPT_PYRO_STRING, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
        else:
            set_state(uid, "phone", type=data)
            await app.send_message(uid, PROMPT_PHONE, reply_markup=CANCEL_BTN, parse_mode=ParseMode.HTML)
    except Exception as e:
        await handle_error(e, uid, "session_cb")
