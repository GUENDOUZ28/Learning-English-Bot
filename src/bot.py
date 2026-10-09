"""Main Telegram bot application builder and runner."""

import logging
from typing import Optional
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from src.config import TELEGRAM_BOT_TOKEN
from src.database import Database
from src.scheduler import setup_scheduler
from src.handlers.start import start_command, help_command
from src.handlers.daily import daily_command, audio_callback, difficult_callback
from src.handlers.quiz import quiz_command, quiz_answer_callback, quiz_next_callback
from src.handlers.review import review_command, difficult_command
from src.handlers.progress import progress_command
from src.handlers.settings import settings_command, settings_callback, settime_command

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Optional[object], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


async def post_init(application: Application) -> None:
    """Run initial database setup and register bot commands menu in Telegram."""
    db: Database = application.bot_data["db"]
    await db.init_db()

    # Setup Telegram command menu
    commands = [
        BotCommand("daily", "Get today's 5 vocabulary words"),
        BotCommand("quiz", "Take an interactive quiz"),
        BotCommand("review", "Review previously learned words"),
        BotCommand("difficult", "Review difficult vocabulary"),
        BotCommand("progress", "View your stats and streak"),
        BotCommand("settings", "Preferences & translations"),
        BotCommand("help", "Bot usage instructions"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands menu registered successfully.")
    except Exception as e:
        logger.warning(f"Could not set bot commands menu: {e}")


def build_application(token: Optional[str] = None, db_instance: Optional[Database] = None) -> Application:
    """Build and configure the Telegram application."""
    bot_token = token or TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured! Please provide it in .env or environment.")

    db = db_instance or Database()

    application = (
        ApplicationBuilder()
        .token(bot_token)
        .post_init(post_init)
        .build()
    )

    # Store database instance in bot_data
    application.bot_data["db"] = db

    # 1. Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("difficult", difficult_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("settime", settime_command))

    # 2. Reply Keyboard Text Handlers
    application.add_handler(MessageHandler(filters.Regex("^📖 Today's 5 Words$"), daily_command))
    application.add_handler(MessageHandler(filters.Regex("^🎯 Quick Quiz$"), quiz_command))
    application.add_handler(MessageHandler(filters.Regex("^🔄 Review Words$"), review_command))
    application.add_handler(MessageHandler(filters.Regex("^⚠️ Difficult Words$"), difficult_command))
    application.add_handler(MessageHandler(filters.Regex("^📊 My Progress$"), progress_command))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_command))

    # 3. Inline Callback Handlers
    application.add_handler(CallbackQueryHandler(audio_callback, pattern=r"^audio:\d+$"))
    application.add_handler(CallbackQueryHandler(difficult_callback, pattern=r"^diff:\d+$"))
    application.add_handler(CallbackQueryHandler(quiz_answer_callback, pattern=r"^q:\d+:\d+:[a-z]+$"))
    application.add_handler(CallbackQueryHandler(quiz_next_callback, pattern=r"^quiz_next$"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^(set_lang:|toggle_notif|set_time:)"))

    # 4. Error Handler
    application.add_error_handler(error_handler)

    # 5. Background Scheduler for automated daily deliveries
    setup_scheduler(application)

    return application
