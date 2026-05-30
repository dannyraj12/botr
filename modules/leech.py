import os
import time
from pyrogram import filters
from main import app
from database import users_col
from modules.downloader import download_file
from modules.upload import upload_telegram
from modules.status import build_status
from modules.task_manager import add_task, remove_task


@app.on_message(filters.command("leech"))
async def leech_handler(_, message):
    try:
        args = message.text.split()

        url = args[-1]

        user = await users_col.find_one({"user_id": message.from_user.id})

        task_id = int(time.time()) % 10000

        task = {
            "id": task_id,
            "name": url.split("/")[-1],
            "done": 0,
            "total": 0,
            "action": "Leech",
            "mode": user.get("upload_mode", "document"),
            "start": time.time(),
            "cancel": False
        }

        add_task(task_id, task)

        status_msg = await message.reply("Starting...")

        path = f"downloads/{task_id}_{task['name']}"

        await download_file(task, url, path)

        await upload_telegram(app, task, path, user)

        await status_msg.edit("Completed")

        remove_task(task_id)

    except Exception as e:
        await message.reply(str(e))
