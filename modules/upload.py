import os
import asyncio
import logging
import time

from pyrogram.errors import FloodWait

log = logging.getLogger(__name__)


def _apply_caption_style(text, style):
    if not text:
        return ""
    if style == "bold":
        return "**{}**".format(text)
    if style == "mono":
        return "`{}`".format(text)
    return text


def _progress_bar(percent):
    filled = int(percent / 10)
    return "⬢" * filled + "⬡" * (10 - filled)


def _human(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return "{:.2f} {}".format(size, unit)
        size /= 1024
    return "{:.2f} TB".format(size)


def _eta(done, total, start):
    if done <= 0 or total <= 0:
        return "..."
    elapsed = time.time() - start
    speed = done / elapsed if elapsed > 0 else 0
    if speed <= 0:
        return "..."
    secs = int((total - done) / speed)
    if secs < 60:
        return "{}s".format(secs)
    return "{}m {}s".format(secs // 60, secs % 60)


def _elapsed(start):
    secs = int(time.time() - start)
    if secs < 60:
        return "{}s".format(secs)
    return "{}m {}s".format(secs // 60, secs % 60)


async def upload_telegram(app, task, file_path, user, status_msg=None):
    mode = user.get("upload_mode", "document")
    raw_caption = user.get("caption", "") or ""
    style = user.get("caption_style", "normal")
    caption = _apply_caption_style(raw_caption, style)
    dump_id = user.get("dump_id")
    chat_id = dump_id if dump_id else task.get("chat_id")

    if not chat_id:
        raise ValueError("No dump channel set and no fallback chat_id in task.")

    original_name = task.get("name", os.path.basename(file_path))
    file_size = os.path.getsize(file_path)
    upload_start = time.time()

    # Progress callback that updates the status message
    async def progress(current, total):
        if status_msg is None:
            return
        try:
            percent = (current / total * 100) if total > 0 else 0
            text = (
                "**{}**\n\n"
                "`{}`\n\n"
                "**Progress:** {:.2f}%\n"
                "**Uploaded:** {}\n"
                "**Total Size:** {}\n"
                "**ETA:** {}\n"
                "**Elapsed:** {}\n\n"
                "**Action:** Uploading\n"
                "**Mode:** {}\n"
                "**Engine:** Python\n\n"
                "`/c{}`"
            ).format(
                original_name,
                _progress_bar(percent),
                percent,
                _human(current),
                _human(total),
                _eta(current, total, upload_start),
                _elapsed(upload_start),
                mode.capitalize(),
                task.get("id", "?")
            )
            await status_msg.edit(text)
        except Exception:
            pass  # never crash upload due to status update failure

    while True:
        try:
            if mode == "video":
                await app.send_video(
                    chat_id,
                    video=file_path,
                    caption=caption,
                    file_name=original_name,
                    supports_streaming=True,
                    progress=progress,
                )
            else:
                await app.send_document(
                    chat_id,
                    document=file_path,
                    caption=caption,
                    file_name=original_name,
                    progress=progress,
                )
            return

        except FloodWait as e:
            log.warning("FloodWait: sleeping %ds", e.value)
            await asyncio.sleep(e.value)

        except Exception as e:
            log.error("Upload error: %s - retrying in 5s", e)
            await asyncio.sleep(5)
