"""Handlers for spaced repetition review and difficult words drills."""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.database import Database
from src.formatters import format_word_card, format_difficult_words_summary
from src.keyboards import get_word_actions_keyboard, get_main_menu_keyboard


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /review command or 'Review Words' button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    user_info = await db.get_or_create_user(user.id)
    lang = user_info.get("preferred_lang", "both")

    words = await db.get_review_words(user.id, limit=5)
    if not words:
        await update.message.reply_text(
            text="🌱 <b>No words to review yet!</b>\n\nStart by tapping <b>📖 Today's 5 Words</b> to learn your first lesson.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        text=f"🔄 <b>Review Session (5 Words)</b>\n\nReviewing previously learned vocabulary reinforces long-term retention:",
        parse_mode=ParseMode.HTML
    )

    for idx, w in enumerate(words, 1):
        is_diff = await db.is_word_difficult(user.id, w["id"])
        card = format_word_card(w, lang=lang, is_difficult=is_diff, index=idx)
        kb = get_word_actions_keyboard(w["id"], is_difficult=is_diff)
        await update.message.reply_text(text=card, parse_mode=ParseMode.HTML, reply_markup=kb)

    await update.message.reply_text(
        text="✨ Great review! Tap <b>🎯 Quick Quiz</b> whenever you'd like to test yourself.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )


async def difficult_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /difficult command or 'Difficult Words' button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    diff_words = await db.get_difficult_words(user.id, limit=15)
    summary_text = format_difficult_words_summary(diff_words)

    keyboard = None
    if diff_words:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Practice With a Quiz Now", callback_data="quiz_next")]
        ])

    await update.message.reply_text(
        text=summary_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard or get_main_menu_keyboard()
    )
