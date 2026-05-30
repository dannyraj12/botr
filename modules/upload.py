import os
import asyncio
import logging

from pyrogram.errors import FloodWait

log = logging.getLogger(__name__)


def _apply_caption_style(text: str, style: str) -> str:
    if not text:
        return ""
    if style == "bold":
        return f"**{text}**"
    if style == "mono":
        return f"`{text}`"
    return text  # normal


async def upload_telegram(app, task: dict, file_path: str, user: dict):
    """
    Upload file_path to Telegram.
    Sends to dump_id if set, else replies to the original message.
    Respects upload_mode (video / document) and caption settings.
    """
    mode = user.get("upload_mode", "document")
    raw_caption = user.get("caption", "") or ""
    style = user.get("caption_style", "normal")
    caption = _apply_caption_style(raw_caption, style)
    dump_id = user.get("dump_id")
    chat_id = dump_id if dump_id else task.get("chat_id")

    if not chat_id:
        raise ValueError("No dump channel set and no fallback chat_id in task.")

    # Preserve original filename for Telegram display
    original_name = task.get("name", os.path.basename(file_path))

    while True:
        try:
            if mode == "video":
                await app.send_video(
                    chat_id,
                    video=file_path,
                    caption=caption,
                    file_name=original_name,
                    supports_streaming=True,
                )
            else:
                await app.send_document(
                    chat_id,
                    document=file_path,
                    caption=caption,
                    file_name=original_name,
                )
            return

        except FloodWait as e:
            log.warning("FloodWait: sleeping %ds", e.value)
            await asyncio.sleep(e.value)

        except Exception as e:
            log.error("Upload error: %s — retrying in 5s", e)
            await asyncio.sleep(5)
