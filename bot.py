import logging, importlib
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from plugins.client import app

def load_all_plugins():
    """Manually import every plugin file — guarantees handler registration."""
    plugin_dir = Path(__file__).parent / "plugins"
    loaded = 0
    failed = 0
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

if __name__ == "__main__":
    load_all_plugins()
    logging.info("Starting Session Bot...")
    app.run()
