import logging
from plugins.client import app
from plugins.database import is_enabled

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    logging.info(f"Starting Session Bot... MongoDB={'ON' if is_enabled() else 'OFF'}")
    app.run()
