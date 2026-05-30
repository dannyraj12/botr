import psutil
import shutil
import time


def human(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024


def progress_bar(percent):
    filled = int(percent / 10)
    return "⬢" * filled + "⬡" * (10 - filled)


async def build_status(task):
    percent = 0

    if task["total"] > 0:
        percent = (task["done"] / task["total"]) * 100

    free = shutil.disk_usage("/").free

    text = f"""
{task['name']}

{progress_bar(percent)}

Progress: {percent:.2f}%
Processed: {human(task['done'])}
Total Size: {human(task['total'])}
ETA: {task.get('eta', 'Unknown')}
Elapsed: {int(time.time() - task['start'])}s

Action: {task['action']}
Mode: {task['mode']}
Engine: Python

FREE: {human(free)}
CPU: {psutil.cpu_percent()}%
RAM: {psutil.virtual_memory().percent}%

/c{task['id']}
"""

    return text
