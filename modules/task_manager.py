from database import tasks_col

active_tasks = {}

_counter = 0


def _next_id():
    global _counter
    _counter = (_counter % 9999) + 1
    return _counter


def add_task(task_id, task):
    active_tasks[task_id] = task


def remove_task(task_id):
    active_tasks.pop(task_id, None)


def get_task(task_id):
    return active_tasks.get(task_id)


def get_all_tasks():
    return active_tasks


def new_task_id():
    return _next_id()


async def persist_task(task):
    await tasks_col.update_one(
        {"id": task["id"]},
        {"$set": task},
        upsert=True
    )


async def clear_persisted_task(task_id):
    await tasks_col.delete_one({"id": task_id})


async def restore_tasks():
    cursor = tasks_col.find({"status": {"$in": ["downloading", "uploading"]}})
    return await cursor.to_list(length=100)
