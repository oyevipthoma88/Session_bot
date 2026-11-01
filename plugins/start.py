from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyrogram.enums import ParseMode
from .client import app
from . import config
from .database import save_user, get_start_pic
from .helpers import WELCOME, MAIN_MENU, BACK_BTN, is_member, force_sub_check, handle_error

@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    try:
        await save_user(message.from_user)
        if not await force_sub_check(message):
            return
        pic = await get_start_pic() or (config.START_PIC or None)
        if pic:
            try:
                await message.reply_photo(pic, caption=WELCOME,
                                          reply_markup=MAIN_MENU, parse_mode=ParseMode.HTML)
                return
            except Exception:
                pass
        await message.reply_text(WELCOME, reply_markup=MAIN_MENU,
                                 parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await handle_error(e, message.from_user.id, "start")


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message):
    try:
        txt = (
            "<b>❓ Help &amp; About</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Commands</b>\n"
            "├ /start — Main Menu\n"
            "└ /help — This message\n\n"
            "<b>Session Types</b>\n"
            "├ 🐍 <b>Pyrogram User</b> — Userbot\n"
            "├ 🤖 <b>Pyrogram Bot</b> — Bot token\n"
            "├ 📞 <b>Telethon</b> — Userbot\n"
            "└ 🔄 <b>Converter</b> — Pyrogram → Telethon\n\n"
            "<b>Safety</b>\n"
            "├ Never share your session\n"
            "├ Revoke via Settings → Devices\n"
            "└ Use 2FA for extra safety"
        )
        await message.reply_text(txt, reply_markup=BACK_BTN,
                                 parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await handle_error(e, message.from_user.id, "help")


@app.on_callback_query()
async def common_callbacks(_, query: CallbackQuery):
    data = query.data
    if data in ("pyro_user", "pyro_bot", "telethon", "convert"):
        return
    try:
        await query.answer()
        await save_user(query.from_user)

        if data == "verify_sub":
            if await is_member(query.from_user.id):
                await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU,
                                              parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await query.answer("❌ Abhi tak channel join nahi kiya!", show_alert=True)
            return

        if data == "cancel":
            try:
                await query.message.delete()
            except Exception:
                pass
            await app.send_message(query.from_user.id,
                                   "❌ <b>Cancelled.</b>\n\n/start se dobara shuru karein.",
                                   reply_markup=BACK_BTN, parse_mode=ParseMode.HTML)
            return

        if data == "back":
            await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU,
                                          parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        if data == "help":
            txt = (
                "<b>❓ Help</b>\n\n"
                "Menu se session type chunein.\n"
                "Har step pe <b>❌ Cancel</b> button kaam karta hai."
            )
            await query.message.edit_text(txt, reply_markup=BACK_BTN,
                                          parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return
    except Exception as e:
        await handle_error(e, query.from_user.id, "common_callbacks")
