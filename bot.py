import logging, importlib
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from plugins.client import app

def load_all_plugins():
    plugin_dir = Path(__file__).parent / "plugins"
    loaded = failed = 0
    for f in sorted(plugin_dir.glob("*.py")):
        name = f.stem
        if name in ("__init__", "client"):
            continue
        try:
            importlib.import_module(f"plugins.{name}")
            logging.info(f"[PLUGIN LOADED] plugins.{name}")
            loaded += 1
        except Exception as e:
            logging.exception(f"[PLUGIN FAIL] plugins.{name} → {type(e).__name__}: {e}")
            failed += 1
    logging.info(f"[PLUGIN SUMMARY] Loaded={loaded} Failed={failed}")

async def _warmup():
    from plugins.config import LOG_CHANNEL_ID
    if not LOG_CHANNEL_ID:
        logging.warning("[WARMUP] LOG_CHANNEL_ID not set — log channel disabled")
        return
    try:
        chat = await app.get_chat(LOG_CHANNEL_ID)
        logging.info(f"[WARMUP] Log channel OK → id={chat.id} title={chat.title!r}")
    except Exception as e:
        logging.error(f"[WARMUP] Log channel FAIL → {type(e).__name__}: {e}")
        logging.error("[WARMUP] Fix: bot ko channel me ADMIN banao + 'Post Messages' permission do, aur LOG_CHANNEL_ID (-100... ya @username) check karo")

if __name__ == "__main__":
    load_all_plugins()
    logging.info("Starting Session Bot...")
    app.run(_warmup())
