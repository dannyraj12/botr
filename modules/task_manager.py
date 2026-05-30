active_tasks = {}


def add_task(task_id, task):
    active_tasks[task_id] = task


def remove_task(task_id):
    active_tasks.pop(task_id, None)


def get_task(task_id):
    return active_tasks.get(task_id)
