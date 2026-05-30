from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import app
from database import users_col


@app.on_message(filters.command("set"))
async def settings_menu(_, message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Upload Mode", callback_data="upload")],
        [InlineKeyboardButton("Dump Channel", callback_data="dump")],
        [InlineKeyboardButton("Caption", callback_data="caption")],
        [InlineKeyboardButton("Drive", callback_data="drive")]
    ])

    await message.reply("Settings", reply_markup=kb)
