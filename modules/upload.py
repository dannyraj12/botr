import os
from pyrogram.errors import FloodWait
import asyncio


async def upload_telegram(app, task, file_path, settings):
    while True:
        try:
            caption = settings.get("caption", "")
            mode = settings.get("upload_mode", "document")

            original_name = task["name"]

            if mode == "video":
                await app.send_video(
                    settings["dump_id"],
                    video=file_path,
                    caption=caption,
                    file_name=original_name
                )
            else:
                await app.send_document(
                    settings["dump_id"],
                    document=file_path,
                    caption=caption,
                    file_name=original_name
                )

            return

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception:
            await asyncio.sleep(5)
