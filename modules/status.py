import psutil
import shutil
import time
import os


def human(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return "{:.2f} {}".format(size, unit)
        size /= 1024
    return "{:.2f} TB".format(size)


def progress_bar(percent):
    filled = int(percent / 10)
    return "⬢" * filled + "⬡" * (10 - filled)


def elapsed_str(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return "{}s".format(seconds)
    m, s = divmod(seconds, 60)
    if m < 60:
        return "{}m {}s".format(m, s)
    h, m = divmod(m, 60)
    return "{}h {}m {}s".format(h, m, s)


def eta_str(done, total, start):
    if done <= 0 or total <= 0:
        return "..."
    elapsed = time.time() - start
    speed = done / elapsed if elapsed > 0 else 0
    remaining = total - done
    if speed <= 0:
        return "∞"
    eta = remaining / speed
    return elapsed_str(eta)


def get_free_disk(path="/app"):
    """
    Try to find the largest available partition — not just root.
    Falls back through common paths used on hosting platforms.
    """
    candidates = [path, "/app", "/home", "/tmp", "/mnt", "/"]
    best_free = 0
    for p in candidates:
        try:
            free = shutil.disk_usage(p).free
            if free > best_free:
                best_free = free
        except Exception:
            continue
    return best_free


async def build_status(task):
    done = task.get("done", 0)
    total = task.get("total", 0)
    start = task.get("start", time.time())

    percent = (done / total * 100) if total > 0 else 0
    free = get_free_disk()

    return (
        "**{}**\n\n"
        "`{}`\n\n"
        "**Progress:** {:.2f}%\n"
        "**Processed:** {}\n"
        "**Total Size:** {}\n"
        "**ETA:** {}\n"
        "**Elapsed:** {}\n\n"
        "**Action:** {}\n"
        "**Mode:** {}\n"
        "**Engine:** Python\n\n"
        "💾 FREE: {}\n"
        "🖥 CPU: {}%\n"
        "🧠 RAM: {}%\n\n"
        "`/c{}`"
    ).format(
        task["name"],
        progress_bar(percent),
        percent,
        human(done),
        human(total),
        eta_str(done, total, start),
        elapsed_str(time.time() - start),
        task.get("action", "—"),
        task.get("mode", "—").capitalize(),
        human(free),
        psutil.cpu_percent(),
        psutil.virtual_memory().percent,
        task["id"]
    )
