import os
import asyncio
import time
import logging

from pyrogram import filters
from pyrogram.errors import MessageNotModified

from bot import app
from database import get_user
from config import DOWNLOAD_DIR, STATUS_UPDATE_INTERVAL
from modules.downloader import download_file
from modules.status import build_status
from modules.task_manager import add_task, remove_task, new_task_id, get_task
from modules.zip_utils import zip_file, extract_file
from modules.cleanup import cleanup

log = logging.getLogger(__name__)


def _parse_args(text: str):
    parts = text.split()[1:]
    do_zip = "-z" in parts
    do_extract = "-e" in parts
    url = None
    for p in reversed(parts):
        if not p.startswith("-"):
            url = p
            break
    return url, do_zip, do_extract


async def _status_loop(task: dict, status_msg):
    while not task.get("done_flag"):
        try:
            text = await build_status(task)
            await status_msg.edit(text)
        except MessageNotModified:
            pass
        except Exception as e:
            log.debug("Status update skipped: %s", e)
        await asyncio.sleep(STATUS_UPDATE_INTERVAL)


async def _upload_to_drive(file_path: str, user: dict, task: dict) -> str:
    """
    Upload file to Google Drive using stored token.pickle.
    Returns the public/sharable link.
    """
    import pickle
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    token_path = f"sessions/token_{user['user_id']}.pickle"
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            "Google Drive token not found. Upload token.pickle via /set → Drive."
        )

    with open(token_path, "rb") as f:
        creds = pickle.load(f)

    service = build("drive", "v3", credentials=creds)

    folder_id = user.get("drive_folder_id")
    file_meta = {"name": task["name"]}
    if folder_id:
        file_meta["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)
    uploaded = service.files().create(
        body=file_meta,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    # Make file publicly readable
    service.permissions().create(
        fileId=uploaded["id"],
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return uploaded.get("webViewLink", f"https://drive.google.com/file/d/{uploaded['id']}/view")


@app.on_message(filters.command("mirror") & filters.private)
async def mirror_handler(_, message):
    url, do_zip, do_extract = _parse_args(message.text or "")

    if not url or not url.startswith("http"):
        await message.reply("Usage: `/mirror [-z] [-e] URL`")
        return

    user = await get_user(message.from_user.id)

    token_path = f"sessions/token_{user['user_id']}.pickle"
    if not os.path.exists(token_path):
        await message.reply(
            "⚠️ **Google Drive not configured.**\n"
            "Upload your `token.pickle` via /set → Drive first."
        )
        return

    task_id = new_task_id()
    raw_name = url.split("?")[0].split("/")[-1] or f"file_{task_id}"

    task = {
        "id": task_id,
        "name": raw_name,
        "done": 0,
        "total": 0,
        "action": "Mirror",
        "mode": "drive",
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

    status_msg = await message.reply(f"🚀 Starting mirror `{task_id}`...")
    status_loop = asyncio.create_task(_status_loop(task, status_msg))

    try:
        task["status"] = "downloading"
        await download_file(task, url, dl_path)

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

        task["action"] = "Uploading to Drive"
        task["status"] = "uploading"
        link = await _upload_to_drive(process_path, user, task)

        task["done_flag"] = True
        await asyncio.sleep(0.2)
        await status_msg.edit(
            f"✅ **Mirror complete!**\n\n"
            f"📁 **File:** `{task['name']}`\n"
            f"🔗 **Link:** {link}\n\n"
            f"`/c{task_id}`"
        )

    except asyncio.CancelledError:
        task["done_flag"] = True
        await status_msg.edit(f"❌ Task `/c{task_id}` cancelled.")

    except Exception as e:
        task["done_flag"] = True
        log.exception("Mirror error for task %d", task_id)
        await status_msg.edit(f"❌ Error: `{e}`")

    finally:
        status_loop.cancel()
        remove_task(task_id)
        cleanup(task_dir)
