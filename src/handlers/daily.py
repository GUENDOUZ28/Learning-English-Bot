"""Daily words delivery and word card interaction handlers."""

import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.config import DAILY_WORDS_COUNT
from src.database import Database
from src.audio_service import audio_service
from src.formatters import format_daily_lesson_intro, format_word_card
from src.keyboards import get_word_actions_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def send_daily_lesson(user_id: int, db: Database, bot, force_new: bool = False) -> None:
    """Send daily 5 words lesson to a specific user (used by both handler and scheduler)."""
    user_data = await db.get_or_create_user(user_id)
    lang = user_data.get("preferred_lang", "both")
    streak = user_data.get("streak", 0)

    words = await db.get_daily_words_for_user(user_id, count=DAILY_WORDS_COUNT, force_new=force_new)
    if not words:
        await bot.send_message(
            chat_id=user_id,
            text="⚠️ No vocabulary words available at the moment. Please contact the administrator.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Send lesson header
    intro_text = format_daily_lesson_intro(len(words), streak)
    await bot.send_message(
        chat_id=user_id,
        text=intro_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )

    # Send each word card with interactive action buttons
    for idx, word_data in enumerate(words, 1):
        is_diff = await db.is_word_difficult(user_id, word_data["id"])
        card_text = format_word_card(word_data, lang=lang, is_difficult=is_diff, index=idx)
        keyboard = get_word_actions_keyboard(word_data["id"], is_difficult=is_diff)

        await bot.send_message(
            chat_id=user_id,
            text=card_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    # Completion advice
    await bot.send_message(
        chat_id=user_id,
        text=(
            "🎉 <b>Great job reviewing today's 5 words!</b>\n\n"
            "Ready to lock them in your memory? Tap <b>🎯 Quick Quiz</b> to practice right away!"
        ),
        parse_mode=ParseMode.HTML
    )


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily command or 'Today's 5 Words' menu button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    await send_daily_lesson(user.id, db, context.bot, force_new=False)


async def audio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Listen Pronunciation' inline button callback."""
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        word_id = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.answer("Invalid audio request.", show_alert=True)
        return

    db: Database = context.bot_data["db"]
    word_data = await db.get_word_by_id(word_id)
    if not word_data:
        await query.answer("Word not found.", show_alert=True)
        return

    word_text = word_data["word"]
    await query.answer(f"Pronouncing '{word_text}'...")

    # Generate or fetch audio
    audio_path = await audio_service.get_word_pronunciation_path(word_text)
    if audio_path and audio_path.exists():
        with open(audio_path, "rb") as voice_file:
            caption = f"🔊 <b>{word_text.upper()}</b> {word_data.get('phonetic', '')}"
            await context.bot.send_voice(
                chat_id=query.message.chat_id,
                voice=voice_file,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"🔊 Pronunciation for <b>{word_text.upper()}</b>: {word_data.get('phonetic', '')} <i>(Audio unavailable)</i>",
            parse_mode=ParseMode.HTML
        )


async def difficult_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Mark as Difficult' inline button callback."""
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        word_id = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.answer("Invalid request.", show_alert=True)
        return

    user = update.effective_user
    db: Database = context.bot_data["db"]

    word_data = await db.get_word_by_id(word_id)
    if not word_data:
        await query.answer("Word not found.", show_alert=True)
        return

    new_status = await db.toggle_word_difficult(user.id, word_id)

    # Update inline keyboard on the word card
    updated_keyboard = get_word_actions_keyboard(word_id, is_difficult=new_status)
    try:
        await query.edit_message_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        logger.debug(f"Could not edit reply markup: {e}")

    alert_msg = (
        f"⭐ '{word_data['word']}' marked as difficult! It will be prioritized in your reviews."
        if new_status
        else f"✅ '{word_data['word']}' removed from difficult words list."
    )
    await query.answer(alert_msg, show_alert=True)
