import os
import asyncio
import time
import logging

from pyrogram import filters
from pyrogram.errors import MessageNotModified

from bot import app
from database import get_user
from config import FREE_SPLIT_SIZE, PREMIUM_SPLIT_SIZE, STATUS_UPDATE_INTERVAL, DOWNLOAD_DIR
from modules.downloader import download_file
from modules.upload import upload_telegram
from modules.status import build_status
from modules.task_manager import add_task, remove_task, new_task_id, get_task
from modules.split_utils import split_file
from modules.zip_utils import zip_file, extract_file
from modules.cleanup import cleanup

log = logging.getLogger(__name__)


def _parse_args(text: str):
    """
    Parse command text.
    Returns (url, do_zip, do_extract)
    Example: /leech -z -e https://example.com/file.zip
    """
    parts = text.split()
    # Drop the command itself (/leech)
    parts = parts[1:]

    do_zip = "-z" in parts
    do_extract = "-e" in parts

    # URL is the last non-flag token
    url = None
    for p in reversed(parts):
        if not p.startswith("-"):
            url = p
            break

    return url, do_zip, do_extract


async def _status_loop(task: dict, status_msg):
    """Background task: edit status message every STATUS_UPDATE_INTERVAL seconds."""
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

    # Check dump channel
    if not user.get("dump_id"):
        await message.reply(
            "⚠️ **Dump channel not set.**\n"
            "Use /set → Dump Channel to configure it first."
        )
        return

    task_id = new_task_id()
    raw_name = url.split("?")[0].split("/")[-1] or f"file_{task_id}"

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

    task_dir = os.path.join(DOWNLOAD_DIR, f"task_{task_id}")
    os.makedirs(task_dir, exist_ok=True)
    dl_path = os.path.join(task_dir, raw_name)

    status_msg = await message.reply(f"🚀 Starting leech `{task_id}`...")

    # Start live status updater
    status_loop = asyncio.create_task(_status_loop(task, status_msg))

    try:
        # ── Download ──────────────────────────────────────────────────────────
        task["status"] = "downloading"
        await download_file(task, url, dl_path)

        # ── Post-process ──────────────────────────────────────────────────────
        process_path = dl_path

        if do_extract:
            task["action"] = "Extracting"
            process_path = await asyncio.get_event_loop().run_in_executor(
                None, extract_file, dl_path, task_dir
            )
            task["name"] = os.path.basename(process_path)

        if do_zip:
            task["action"] = "Zipping"
            process_path = await asyncio.get_event_loop().run_in_executor(
                None, zip_file, process_path
            )
            task["name"] = os.path.basename(process_path)

        # ── Split if needed ───────────────────────────────────────────────────
        # Determine split size (premium check placeholder — always free for now)
        split_size = FREE_SPLIT_SIZE
        file_size = os.path.getsize(process_path)

        if file_size > split_size:
            task["action"] = "Splitting"
            parts = await asyncio.get_event_loop().run_in_executor(
                None, split_file, process_path, split_size
            )
        else:
            parts = [process_path]

        # ── Upload ────────────────────────────────────────────────────────────
        task["action"] = "Uploading"
        for i, part in enumerate(parts, 1):
            part_task = dict(task)
            part_task["name"] = os.path.basename(part)
            if len(parts) > 1:
                part_task["name"] += f" [{i}/{len(parts)}]"
            await upload_telegram(app, part_task, part, user)

        task["done_flag"] = True
        await asyncio.sleep(0.2)  # let status loop exit cleanly

        final = await build_status({**task, "action": "Done ✅", "done": task["total"] or file_size})
        await status_msg.edit(final)

    except asyncio.CancelledError:
        task["done_flag"] = True
        await status_msg.edit(f"❌ Task `/c{task_id}` cancelled.")

    except Exception as e:
        task["done_flag"] = True
        log.exception("Leech error for task %d", task_id)
        await status_msg.edit(f"❌ Error: `{e}`")

    finally:
        status_loop.cancel()
        remove_task(task_id)
        cleanup(task_dir)


# ── Cancel handler ─────────────────────────────────────────────────────────────

@app.on_message(filters.private & filters.regex(r"^/c(\d+)$"))
async def cancel_handler(_, message):
    try:
        task_id = int(message.matches[0].group(1))
    except (IndexError, ValueError):
        return

    task = get_task(task_id)
    if task is None:
        await message.reply(f"No active task with ID `{task_id}`.")
        return

    task["cancel"] = True
    await message.reply(f"⏹ Cancelling task `/c{task_id}`...")
