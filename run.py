"""Entrypoint to launch the English Vocabulary Telegram Bot."""

import sys
import asyncio
import logging
from src.config import TELEGRAM_BOT_TOKEN, DATABASE_PATH
from src.database import Database
from src.bot import build_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("vocab_bot")


async def init_only():
    """Initialize database and vocabulary catalog without starting network polling."""
    db = Database()
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    await db.init_db()
    stats = await db.get_user_stats(0)
    logger.info(f"Database ready! Catalog contains {stats['total_catalog']} words.")


def main():
    if "--init-db" in sys.argv:
        asyncio.run(init_only())
        return

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n" + "=" * 65)
        print("⚠️  TELEGRAM BOT TOKEN REQUIRED")
        print("=" * 65)
        print("To run the bot, you need a Telegram Bot Token:")
        print("1. Open Telegram and search for @BotFather (https://t.me/BotFather)")
        print("2. Send '/newbot' and follow instructions to name your bot")
        print("3. Copy the HTTP API token provided by BotFather")
        print("4. Paste the token into your '.env' file:")
        print("     TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print("5. Then run this script again: python run.py")
        print("=" * 65 + "\n")
        sys.exit(1)

    logger.info("Starting English Vocabulary Learning Telegram Bot...")
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
