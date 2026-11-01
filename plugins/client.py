import os
import asyncio
from pyrogram import Client, StopPropagation
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler

# ============================================================
# Fork-independent Client.listen() patch
# Replaces pyromod (incompatible with PyroTGFork)
# ============================================================
async def _listen(self, chat_id=None, user_id=None, filters=None, timeout=60):
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    async def _handler(client, message):
        try:
            if chat_id is not None and message.chat and message.chat.id != chat_id:
                return
            if user_id is not None:
                if not message.from_user or message.from_user.id != user_id:
                    return
            if filters is not None:
                try:
                    ok = filters(client, message)
                    if asyncio.iscoroutine(ok):
                        ok = await ok
                    if not ok:
                        return
                except Exception:
                    return
            if not future.done():
                future.set_result(message)
            raise StopPropagation
        except StopPropagation:
            raise
        except Exception:
            return

    handler = MessageHandler(_handler)
    self.add_handler(handler)
    try:
        return await asyncio.wait_for(future, timeout)
    finally:
        try:
            self.remove_handler(handler)
        except Exception:
            pass

if not hasattr(Client, "listen"):
    Client.listen = _listen
    print("[PATCH] Client.listen injected (fork-independent)")

app = Client(
    "SessionBot",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", ""),
    in_memory=True,
    parse_mode=ParseMode.HTML
)
