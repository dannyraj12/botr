import psutil
import shutil
import time


def human(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def progress_bar(percent: float) -> str:
    filled = int(percent / 10)
    return "⬢" * filled + "⬡" * (10 - filled)


def elapsed_str(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def eta_str(done: int, total: int, start: float) -> str:
    if done <= 0 or total <= 0:
        return "..."
    elapsed = time.time() - start
    speed = done / elapsed if elapsed > 0 else 0
    remaining = total - done
    if speed <= 0:
        return "∞"
    eta = remaining / speed
    return elapsed_str(eta)


async def build_status(task: dict) -> str:
    done = task.get("done", 0)
    total = task.get("total", 0)
    start = task.get("start", time.time())

    percent = (done / total * 100) if total > 0 else 0
    free = shutil.disk_usage("/").free

    return (
        f"**{task['name']}**\n\n"
        f"`{progress_bar(percent)}`\n\n"
        f"**Progress:** {percent:.2f}%\n"
        f"**Processed:** {human(done)}\n"
        f"**Total Size:** {human(total)}\n"
        f"**ETA:** {eta_str(done, total, start)}\n"
        f"**Elapsed:** {elapsed_str(time.time() - start)}\n\n"
        f"**Action:** {task.get('action', '—')}\n"
        f"**Mode:** {task.get('mode', '—').capitalize()}\n"
        f"**Engine:** Python\n\n"
        f"💾 FREE: {human(free)}\n"
        f"🖥 CPU: {psutil.cpu_percent()}%\n"
        f"🧠 RAM: {psutil.virtual_memory().percent}%\n\n"
        f"`/c{task['id']}`"
    )
