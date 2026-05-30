import logging
import os
import asyncio
from threading import Thread
from aiohttp import web
from pyrogram import Client, idle
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


def start_health_server():
    from aiohttp import web
    import asyncio

    async def health(request):
        return web.Response(text="OK")

    async def run():
        server = web.Application()
        server.router.add_get("/", health)
        runner = web.AppRunner(server)
        await runner.setup()
        port = int(os.environ.get("PORT", 8000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        await asyncio.Event().wait()

    asyncio.run(run())


if __name__ == "__main__":
    # Health server runs in background thread (own event loop)
    t = Thread(target=start_health_server, daemon=True)
    t.start()

    # Pyrogram runs in main thread with its own event loop
    app.run()
