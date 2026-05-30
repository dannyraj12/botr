from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["mirror_bot"]

users_col = db["users"]
tasks_col = db["tasks"]
