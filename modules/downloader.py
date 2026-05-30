import aiohttp
import asyncio
import os
from config import CHUNK_SIZE, MAX_RETRIES


async def download_file(task, url, path):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            existing = 0

            if os.path.exists(path):
                existing = os.path.getsize(path)

            headers = {}

            if existing > 0:
                headers["Range"] = f"bytes={existing}-"

            timeout = aiohttp.ClientTimeout(total=None)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as r:

                    if r.status not in [200, 206]:
                        raise Exception(f"Bad status: {r.status}")

                    total = r.headers.get("Content-Length")

                    if total:
                        task["total"] = int(total) + existing

                    mode = "ab" if existing else "wb"

                    with open(path, mode) as f:
                        async for chunk in r.content.iter_chunked(CHUNK_SIZE):
                            if task.get("cancel"):
                                raise Exception("Cancelled")

                            f.write(chunk)
                            existing += len(chunk)
                            task["done"] = existing

            return path

        except Exception as e:
            retries += 1
            await asyncio.sleep(retries * 5)

    raise Exception("Download failed")
