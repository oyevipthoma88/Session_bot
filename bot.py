import logging
import importlib
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from plugins.client import app

def force_load_plugins():
    plugin_dir = Path(__file__).parent / "plugins"
    for f in sorted(plugin_dir.glob("*.py")):
        name = f.stem
        if name in ("__init__", "client"):
            continue
        try:
            importlib.import_module(f"plugins.{name}")
            logging.info(f"[PLUGIN LOADED] plugins.{name}")
        except Exception as e:
            logging.error(f"[PLUGIN FAIL] plugins.{name} → {type(e).__name__}: {e}")

force_load_plugins()

if __name__ == "__main__":
    logging.info("Starting Session Bot...")
    app.run()
