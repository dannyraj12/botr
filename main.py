from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

app = Client(
    "mirrorbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

import modules.leech
import modules.mirror
import modules.settings

app.run()
