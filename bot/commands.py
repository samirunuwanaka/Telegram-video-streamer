"""
Telegram Bot Command Handlers
Provides interactive slash commands for user management and ESP32 stream control.
"""

import os
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import AUTHORIZED_USER_IDS, DEVICE_ID, TEMP_DATA_DIR
from common.messages import format_status_message
from pc.api_server import receiver_engine
from common.protocol import CommandPacket
from common.messages import ACTION_START_STREAM, ACTION_STOP_STREAM, ACTION_SET_FPS, ACTION_SET_QUALITY
from bot.cleanup import FileCleanupWorker


def is_authorized(user_id: int) -> bool:
    """
    Checks if Telegram user is authorized to issue commands.
    """
    if not AUTHORIZED_USER_IDS:
        return True  # If no IDs specified in .env, default to allow for setup
    return user_id in AUTHORIZED_USER_IDS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user ID.")
        return

    welcome_msg = (
        f"<b>🤖 Telegram Video Communicator Bot</b>\n\n"
        f"Device: <code>{DEVICE_ID}</code>\n"
        f"Commands:\n"
        f"• /stream - Start video streaming\n"
        f"• /stop - Stop video streaming\n"
        f"• /fps &lt;1-30&gt; - Set embedded FPS\n"
        f"• /quality &lt;10-90&gt; - Set JPEG compression quality\n"
        f"• /status - Get stream metrics\n"
        f"• /snapshot - Get live high-res AI frame\n"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML)


async def cmd_stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    cmd = CommandPacket(action=ACTION_START_STREAM)
    receiver_engine.set_pending_command(cmd)
    receiver_engine.is_streaming = True
    await update.message.reply_text("▶️ <b>Stream START</b> command queued for ESP32.", parse_mode=ParseMode.HTML)


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    cmd = CommandPacket(action=ACTION_STOP_STREAM)
    receiver_engine.set_pending_command(cmd)
    receiver_engine.is_streaming = False
    await update.message.reply_text("⏹️ <b>Stream STOP</b> command queued for ESP32.", parse_mode=ParseMode.HTML)


async def cmd_fps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /fps <1-30>")
        return

    new_fps = int(context.args[0])
    if new_fps < 1 or new_fps > 30:
        await update.message.reply_text("FPS must be between 1 and 30.")
        return

    cmd = CommandPacket(action=ACTION_SET_FPS, params={"fps": new_fps})
    receiver_engine.set_pending_command(cmd)
    receiver_engine.current_fps = new_fps
    await update.message.reply_text(f"⚡ Target FPS set to <b>{new_fps}</b>. Sent to ESP32.", parse_mode=ParseMode.HTML)


async def cmd_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /quality <10-90>")
        return

    quality = int(context.args[0])
    cmd = CommandPacket(action=ACTION_SET_QUALITY, params={"quality": quality})
    receiver_engine.set_pending_command(cmd)
    await update.message.reply_text(f"🖼️ JPEG Quality set to <b>{quality}%</b>.", parse_mode=ParseMode.HTML)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    status_data = receiver_engine.get_status()
    msg = format_status_message(
        device_id=status_data["device_id"],
        is_streaming=status_data["is_streaming"],
        fps=status_data["fps"],
        width=640,
        height=480,
        seq=status_data["last_sequence"]
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_snapshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized user.")
        return

    jpeg_bytes = receiver_engine.get_latest_jpeg(use_upscaled=True)
    if not jpeg_bytes:
        await update.message.reply_text("⚠️ No frame captured yet. Ensure ESP32 stream is active.")
        return

    # Save temporary file for upload
    temp_file = TEMP_DATA_DIR / f"snapshot_{int(update.message.date.timestamp())}.jpg"
    with open(temp_file, "wb") as f:
        f.write(jpeg_bytes)

    # Upload to Telegram & Delete immediately afterwards
    try:
        with open(temp_file, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"📷 Live Snapshot (Decrypted & AI Upscaled)\nSequence #{receiver_engine.last_sequence}"
            )
    finally:
        FileCleanupWorker.safe_delete_file(temp_file)
