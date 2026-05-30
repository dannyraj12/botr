from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["mirror_bot"]

users_col = db["users"]
tasks_col = db["tasks"]


async def get_user(user_id: int) -> dict:
    """
    Return user settings doc. Always returns a dict — never None.
    Creates a default doc in DB if user doesn't exist yet.
    """
    user = await users_col.find_one({"user_id": user_id})
    if user is None:
        user = {
            "user_id": user_id,
            "upload_mode": "document",   # "document" | "video"
            "dump_id": None,             # channel/group id to send files
            "caption": "",               # custom caption text
            "caption_style": "normal",   # "normal" | "bold" | "mono"
            "drive_folder_id": None,
        }
        await users_col.insert_one(user)
    return user


async def update_user(user_id: int, data: dict):
    """Upsert user settings fields."""
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )
