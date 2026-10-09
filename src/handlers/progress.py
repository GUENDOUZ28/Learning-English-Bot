"""User learning progress and statistics handler."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.database import Database
from src.formatters import format_progress_report
from src.keyboards import get_main_menu_keyboard


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /progress command or 'My Progress' button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    stats = await db.get_user_stats(user.id)
    report = format_progress_report(stats, first_name=user.first_name)

    await update.message.reply_text(
        text=report,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )
