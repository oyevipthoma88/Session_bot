from pyrogram import filters
from pyrogram.types import CallbackQuery
from .client import app
from .config import OWNER_ID
from .helpers import WELCOME, MAIN_MENU, BACK_BTN, is_member, force_sub_check

@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    if not await force_sub_check(message):
        return
    await message.reply_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message):
    await message.reply_text(
        "❓ **Help & About**\n\n"
        "**Commands:**\n"
        "/start — Main Menu\n"
        "/help — This message\n\n"
        "**Session Types:**\n"
        "• Pyrogram User — Userbot\n"
        "• Pyrogram Bot — Bot token\n"
        "• Telethon — Telethon userbot\n"
        "• Converter — Pyrogram → Telethon\n\n"
        "**Safety:**\n"
        "• Never share your session string\n"
        "• Revoke via Settings → Devices\n"
        "• Use 2FA",
        reply_markup=BACK_BTN,
        disable_web_page_preview=True,
    )

@app.on_callback_query()
async def common_callbacks(_, query: CallbackQuery):
    data = query.data
    await query.answer()

    if data == "verify_sub":
        if await is_member(query.from_user.id):
            await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)
        else:
            await query.answer("❌ Abhi tak channel join nahi kiya!", show_alert=True)
        return

    if data == "cancel":
        try:
            await query.message.delete()
        except Exception:
            pass
        await app.send_message(query.from_user.id, "❌ **Cancelled.**\n\n/start se dobara shuru karein.", reply_markup=BACK_BTN)
        return

    if data == "back":
        await query.message.edit_text(WELCOME, reply_markup=MAIN_MENU, disable_web_page_preview=True)
        return

    if data == "help":
        await query.message.edit_text(
            "❓ **Help & About**\n\n"
            "Menu se session type chunein.\n"
            "Har step pe Cancel button kaam karta hai.",
            reply_markup=BACK_BTN,
            disable_web_page_preview=True,
        )
        return
