import os
import asyncio
import time
import logging

from pyrogram import filters
from pyrogram.errors import MessageNotModified

from bot import app
from database import get_user
from config import FREE_SPLIT_SIZE, STATUS_UPDATE_INTERVAL, DOWNLOAD_DIR
from modules.downloader import download_file
from modules.upload import upload_telegram
from modules.status import build_status
from modules.task_manager import add_task, remove_task, new_task_id, get_task
from modules.split_utils import split_file
from modules.zip_utils import zip_file, extract_file
from modules.cleanup import cleanup

log = logging.getLogger(__name__)


def _parse_args(text):
    parts = text.split()[1:]
    do_zip = "-z" in parts
    do_extract = "-e" in parts
    url = None
    for p in reversed(parts):
        if not p.startswith("-"):
            url = p
            break
    return url, do_zip, do_extract


async def _status_loop(task, status_msg):
    while not task.get("done_flag"):
        try:
            text = await build_status(task)
            await status_msg.edit(text)
        except MessageNotModified:
            pass
        except Exception as e:
            log.debug("Status update skipped: %s", e)
        await asyncio.sleep(STATUS_UPDATE_INTERVAL)


@app.on_message(filters.command("leech") & filters.private)
async def leech_handler(_, message):
    url, do_zip, do_extract = _parse_args(message.text or "")

    if not url or not url.startswith("http"):
        await message.reply("Usage: `/leech [-z] [-e] URL`")
        return

    user = await get_user(message.from_user.id)

    if not user.get("dump_id"):
        await message.reply(
            "⚠️ **Dump channel not set.**\n"
            "Use /set → Dump Channel to configure it first."
        )
        return

    task_id = new_task_id()
    raw_name = url.split("?")[0].split("/")[-1] or "file_{}".format(task_id)

    task = {
        "id": task_id,
        "name": raw_name,
        "done": 0,
        "total": 0,
        "action": "Leech",
        "mode": user.get("upload_mode", "document"),
        "start": time.time(),
        "cancel": False,
        "done_flag": False,
        "chat_id": message.chat.id,
        "status": "downloading",
    }

    add_task(task_id, task)

    task_dir = os.path.join(DOWNLOAD_DIR, "task_{}".format(task_id))
    os.makedirs(task_dir, exist_ok=True)
    dl_path = os.path.join(task_dir, raw_name)

    status_msg = await message.reply("🚀 Starting leech `{}`...".format(task_id))
    status_loop = asyncio.create_task(_status_loop(task, status_msg))

    try:
        # ── Download ──────────────────────────────────────────────────────────
        task["status"] = "downloading"
        await download_file(task, url, dl_path)

        process_path = dl_path

        # ── Extract ───────────────────────────────────────────────────────────
        if do_extract:
            task["action"] = "Extracting"
            # Always use a clean separate subdir to avoid Errno 20
            extract_dir = os.path.join(task_dir, "extracted")
            if os.path.exists(extract_dir):
                import shutil
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)
            process_path = await asyncio.get_event_loop().run_in_executor(
                None, extract_file, dl_path, extract_dir
            )
            task["name"] = os.path.basename(process_path)

        # ── Zip ───────────────────────────────────────────────────────────────
        if do_zip:
            task["action"] = "Zipping"
            process_path = await asyncio.get_event_loop().run_in_executor(
                None, zip_file, process_path
            )
            task["name"] = os.path.basename(process_path)

        # ── Split if needed ───────────────────────────────────────────────────
        file_size = os.path.getsize(process_path)
        if file_size > FREE_SPLIT_SIZE:
            task["action"] = "Splitting"
            parts = await asyncio.get_event_loop().run_in_executor(
                None, split_file, process_path, FREE_SPLIT_SIZE
            )
        else:
            parts = [process_path]

        # ── Upload ────────────────────────────────────────────────────────────
        # Stop download status loop — upload progress takes over
        status_loop.cancel()
        task["action"] = "Uploading"
        task["status"] = "uploading"

        for i, part in enumerate(parts, 1):
            part_task = dict(task)
            part_task["name"] = os.path.basename(part)
            if len(parts) > 1:
                part_task["name"] += " [{}/{}]".format(i, len(parts))
            await upload_telegram(app, part_task, part, user, status_msg)

        task["done_flag"] = True
        await status_msg.edit(
            "✅ **Done!**\n\n"
            "**File:** `{}`\n"
            "**Size:** {:.2f} MB".format(
                task["name"],
                file_size / (1024 * 1024),
            )
        )

    except asyncio.CancelledError:
        task["done_flag"] = True
        await status_msg.edit("❌ Task `/c{}` cancelled.".format(task_id))

    except Exception as e:
        task["done_flag"] = True
        log.exception("Leech error for task %d", task_id)
        await status_msg.edit("❌ Error: `{}`".format(e))

    finally:
        status_loop.cancel()
        remove_task(task_id)
        cleanup(task_dir)


@app.on_message(filters.private & filters.regex(r"^/c(\d+)$"))
async def cancel_handler(_, message):
    try:
        task_id = int(message.matches[0].group(1))
    except (IndexError, ValueError):
        return

    task = get_task(task_id)
    if task is None:
        await message.reply("No active task with ID `{}`.".format(task_id))
        return

    task["cancel"] = True
    await message.reply("⏹ Cancelling task `/c{}`...".format(task_id))
