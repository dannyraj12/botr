from pyrogram import filters
from main import app


@app.on_message(filters.command("mirror"))
async def mirror_handler(_, message):
    await message.reply("Mirror system starter ready")
