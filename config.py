import os

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")

DOWNLOAD_DIR = "downloads"
TEMP_DIR = "temp"
SESSION_DIR = "sessions"

# Telegram file size limits
FREE_SPLIT_SIZE = 2 * 1024 ** 3    # 2 GB
PREMIUM_SPLIT_SIZE = 4 * 1024 ** 3  # 4 GB

# Downloader
CHUNK_SIZE = 1024 * 1024   # 1 MB per chunk
MAX_RETRIES = 20

# Status message update interval (seconds)
STATUS_UPDATE_INTERVAL = 5
