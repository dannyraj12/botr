from pyrogram import filters
from main import app


@app.on_message(filters.command("start"))
async def start_handler(_, message):

    text = """
Hello Bro 👋

Personal Mirror + Leech Bot Ready

Commands:

/leech URL
/mirror URL
/set

Flags:
-e => extract
-z => zip

Cancel:
 /c1
"""

    await message.reply(text)
