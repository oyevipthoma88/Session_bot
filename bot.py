import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
from plugins.client import app
if __name__ == "__main__":
    logging.info("Starting Session Bot...")
    app.run()
