"""Start and help handlers."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.database import Database
from src.keyboards import get_main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command: register user and show welcome message."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    await db.get_or_create_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username
    )

    welcome_text = (
        f"👋 <b>Welcome to English Vocabulary Master, {user.first_name or 'Friend'}!</b>\n\n"
        f"I'm your personal AI English tutor designed to help you expand your vocabulary, "
        f"master pronunciation, and never forget words through daily practice and quizzes.\n\n"
        f"✨ <b>What you can do:</b>\n"
        f"• 📖 <b>Daily English Words:</b> Receive 5 curated words every day with definitions, "
        f"Arabic & French translations, examples, and native voice pronunciation.\n"
        f"• 🎯 <b>Interactive Quizzes:</b> Test your understanding with multiple-choice questions "
        f"and get instant explanations.\n"
        f"• 🔄 <b>Spaced Review & Difficult Words:</b> Track words you struggle with and review them automatically.\n"
        f"• 📊 <b>Streak & Progress:</b> Build daily habits and watch your vocabulary grow.\n\n"
        f"Tap any button below to get started! 👇"
    )

    await update.message.reply_text(
        text=welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command: list commands and tips."""
    help_text = (
        "📚 <b>English Vocabulary Bot Guide</b>\n\n"
        "<b>Available Commands:</b>\n"
        "• /daily - Receive today's 5 vocabulary words\n"
        "• /quiz - Start an interactive vocabulary quiz\n"
        "• /review - Review previously learned words\n"
        "• /difficult - View and practice your difficult words\n"
        "• /progress - Check your streak, mastery rate, and stats\n"
        "• /settings - Customize translations (Arabic/French) & reminder time\n"
        "• /settime <code>HH:MM</code> - Set daily lesson time (e.g. <code>/settime 08:30</code>)\n"
        "• /help - Show this guide\n\n"
        "💡 <i>Tip: You can also use the persistent menu buttons on your keyboard!</i>"
    )

    await update.message.reply_text(
        text=help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )
