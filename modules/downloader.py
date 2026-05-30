import aiohttp
import asyncio
import os
import logging

from config import CHUNK_SIZE, MAX_RETRIES

log = logging.getLogger(__name__)


async def download_file(task: dict, url: str, path: str) -> str:
    """
    Download url → path with resume support, exponential backoff retry,
    and cancellation check every chunk.

    task dict keys used/written:
      task["done"]   — bytes downloaded so far (updated live)
      task["total"]  — total file size in bytes (set when known)
      task["cancel"] — set True externally to abort
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    retries = 0

    while retries < MAX_RETRIES:
        try:
            existing = 0

            if os.path.exists(path):
                existing = os.path.getsize(path)

            headers = {}
            if existing > 0:
                headers["Range"] = f"bytes={existing}-"
                log.info("Resuming from byte %d for %s", existing, url)

            timeout = aiohttp.ClientTimeout(
                total=None,        # no overall limit
                connect=30,
                sock_read=60,
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as r:

                    # 206 = partial content (resume), 200 = full content
                    if r.status == 200 and existing > 0:
                        # Server ignored Range header — restart cleanly
                        log.warning("Server does not support Range; restarting download.")
                        existing = 0

                    elif r.status not in (200, 206):
                        raise Exception(f"HTTP {r.status}")

                    # Parse total size
                    content_length = r.headers.get("Content-Length")
                    if content_length:
                        task["total"] = int(content_length) + existing

                    # Open file: append if resuming, write-new otherwise
                    mode = "ab" if existing > 0 else "wb"
                    task["done"] = existing

                    with open(path, mode) as f:
                        async for chunk in r.content.iter_chunked(CHUNK_SIZE):
                            if task.get("cancel"):
                                raise asyncio.CancelledError("Task cancelled by user")

                            f.write(chunk)
                            existing += len(chunk)
                            task["done"] = existing

            log.info("Download complete: %s (%d bytes)", path, existing)
            return path

        except asyncio.CancelledError:
            raise  # propagate cancel — don't retry

        except Exception as e:
            retries += 1
            wait = min(retries * 5, 60)   # exponential backoff, cap 60s
            log.warning("Download error (attempt %d/%d): %s — retrying in %ds",
                        retries, MAX_RETRIES, e, wait)
            await asyncio.sleep(wait)

    raise Exception(f"Download failed after {MAX_RETRIES} retries: {url}")
