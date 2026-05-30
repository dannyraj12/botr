from pyrogram import filters
from bot import app


@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    text = (
        "Hello 👋\n\n"
        "**Personal Mirror + Leech Bot**\n\n"
        "**Commands:**\n"
        "/leech `URL` — Download & upload to Telegram\n"
        "/mirror `URL` — Download & upload to Google Drive\n"
        "/set — User settings\n\n"
        "**Flags:**\n"
        "`-z` — Zip before upload\n"
        "`-e` — Extract archive before upload\n\n"
        "**Cancel:**\n"
        "`/c1` `/c2` etc — Cancel task by ID"
    )
    await message.reply(text)
