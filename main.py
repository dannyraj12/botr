import logging
import os
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR, TEMP_DIR, SESSION_DIR
import bot as _bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

for d in (DOWNLOAD_DIR, TEMP_DIR, SESSION_DIR):
    os.makedirs(d, exist_ok=True)

app = Client(
    "mirrorbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4,
)

_bot.app = app

import modules.start
import modules.leech
import modules.mirror
import modules.settings

if __name__ == "__main__":
    app.run()
