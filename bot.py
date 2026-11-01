import logging
from plugins.client import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    logging.info("Starting Session Bot (plugin mode)...")
    app.run()
