from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from bot import app
from database import get_user, update_user


def settings_keyboard(user: dict) -> InlineKeyboardMarkup:
    mode = user.get("upload_mode", "document")
    mode_label = "📄 Mode: Document" if mode == "document" else "🎬 Mode: Video"

    dump = user.get("dump_id")
    dump_label = f"📢 Dump: {dump}" if dump else "📢 Dump Channel: Not Set"

    caption = user.get("caption", "")
    caption_label = f"✏️ Caption: {caption[:20]}..." if len(caption) > 20 else f"✏️ Caption: {caption or 'Not Set'}"

    style = user.get("caption_style", "normal")
    style_label = f"🔤 Style: {style.capitalize()}"

    drive_folder = user.get("drive_folder_id")
    drive_label = f"📁 Drive Folder: {str(drive_folder)[:15]}..." if drive_folder else "📁 Drive Folder: Not Set"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(mode_label, callback_data="toggle_mode")],
        [InlineKeyboardButton(dump_label, callback_data="set_dump")],
        [InlineKeyboardButton(caption_label, callback_data="set_caption")],
        [InlineKeyboardButton(style_label, callback_data="cycle_style")],
        [InlineKeyboardButton(drive_label, callback_data="set_drive_folder")],
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")],
    ])


@app.on_message(filters.command("set") & filters.private)
async def settings_menu(_, message):
    user = await get_user(message.from_user.id)
    await message.reply(
        "⚙️ **Your Settings**\nTap a button to change:",
        reply_markup=settings_keyboard(user)
    )


# ── Callback handlers ─────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^toggle_mode$"))
async def cb_toggle_mode(_, query: CallbackQuery):
    user = await get_user(query.from_user.id)
    new_mode = "video" if user.get("upload_mode", "document") == "document" else "document"
    await update_user(query.from_user.id, {"upload_mode": new_mode})
    user["upload_mode"] = new_mode
    await query.edit_message_reply_markup(settings_keyboard(user))
    await query.answer(f"Upload mode → {new_mode.capitalize()}")


@app.on_callback_query(filters.regex("^set_dump$"))
async def cb_set_dump(_, query: CallbackQuery):
    await query.answer("Send your dump channel/group ID in chat.", show_alert=True)
    await query.message.reply(
        "📢 Send the **Dump Channel or Group ID** now.\n\n"
        "Example: `-1001234567890`\n\n"
        "Forward a message from that channel to a bot like @userinfobot to get the ID."
    )
    # The user's next message is handled by the conversation handler below


@app.on_message(filters.private & filters.regex(r"^-?\d{5,}$"))
async def receive_dump_id(_, message):
    """Accept a bare numeric ID as dump channel input."""
    dump_id = int(message.text.strip())
    await update_user(message.from_user.id, {"dump_id": dump_id})
    user = await get_user(message.from_user.id)
    await message.reply(
        f"✅ Dump channel set to `{dump_id}`",
        reply_markup=settings_keyboard(user)
    )


@app.on_callback_query(filters.regex("^set_caption$"))
async def cb_set_caption(_, query: CallbackQuery):
    await query.answer()
    await query.message.reply(
        "✏️ Send your **custom caption** text now.\n\n"
        "Use `/clearcaption` to remove it."
    )


@app.on_message(filters.private & filters.command("clearcaption"))
async def clear_caption(_, message):
    await update_user(message.from_user.id, {"caption": ""})
    await message.reply("✅ Caption cleared.")


@app.on_callback_query(filters.regex("^cycle_style$"))
async def cb_cycle_style(_, query: CallbackQuery):
    user = await get_user(query.from_user.id)
    styles = ["normal", "bold", "mono"]
    current = user.get("caption_style", "normal")
    next_style = styles[(styles.index(current) + 1) % len(styles)]
    await update_user(query.from_user.id, {"caption_style": next_style})
    user["caption_style"] = next_style
    await query.edit_message_reply_markup(settings_keyboard(user))
    await query.answer(f"Caption style → {next_style.capitalize()}")


@app.on_callback_query(filters.regex("^set_drive_folder$"))
async def cb_set_drive_folder(_, query: CallbackQuery):
    await query.answer()
    await query.message.reply(
        "📁 Send your **Google Drive Folder ID** now.\n\n"
        "Get it from the folder's URL:\n"
        "`https://drive.google.com/drive/folders/<FOLDER_ID>`"
    )


@app.on_message(filters.private & filters.regex(r"^[A-Za-z0-9_\-]{20,}$"))
async def receive_drive_folder(_, message):
    """Accept a bare Drive folder ID."""
    folder_id = message.text.strip()
    await update_user(message.from_user.id, {"drive_folder_id": folder_id})
    user = await get_user(message.from_user.id)
    await message.reply(
        f"✅ Drive folder set to `{folder_id}`",
        reply_markup=settings_keyboard(user)
    )


@app.on_callback_query(filters.regex("^close_settings$"))
async def cb_close_settings(_, query: CallbackQuery):
    await query.message.delete()
    await query.answer("Settings closed.")
