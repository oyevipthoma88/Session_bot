import os
import pyromod  # noqa: F401  — MUST be imported before Client
from pyrogram import Client
from pyrogram.enums import ParseMode

app = Client(
    "SessionBot",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", ""),
    in_memory=True,
    parse_mode=ParseMode.HTML,
    plugins=dict(root="plugins", exclude=["client"])
)

# Debug: force plugin discovery check
import importlib, pathlib
_here = pathlib.Path(__file__).parent
for _f in _here.glob("*.py"):
    if _f.stem in ("__init__", "client"):
        continue
    try:
        importlib.import_module(f"plugins.{_f.stem}")
        print(f"[PLUGIN OK] plugins.{_f.stem}")
    except Exception as _e:
        print(f"[PLUGIN FAIL] plugins.{_f.stem} → {type(_e).__name__}: {_e}")
