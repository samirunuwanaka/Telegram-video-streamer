"""
Telegram Bot Service Entry Point
Runs the Telegram Bot instance using python-telegram-bot v20+ Async Application.
"""

import sys
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

from config import TELEGRAM_BOT_TOKEN
from bot.commands import (
    cmd_start,
    cmd_stream,
    cmd_stop,
    cmd_fps,
    cmd_quality,
    cmd_status,
    cmd_snapshot,
)


def run_telegram_bot():
    """
    Builds and starts the Telegram Bot application.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not configured in .env or config.py! Bot interface disabled.")
        return

    print("🤖 Starting Telegram Bot Interface...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stream", cmd_stream))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("fps", cmd_fps))
    app.add_handler(CommandHandler("quality", cmd_quality))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("snapshot", cmd_snapshot))

    print("✅ Telegram Bot initialized and polling for commands...")
    app.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
