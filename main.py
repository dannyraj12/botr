from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

app = Client(
    "mirrorbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Import modules AFTER app is defined so they can safely import app
from modules import start, leech, mirror, settings  # noqa: E402, F401

app.run()
