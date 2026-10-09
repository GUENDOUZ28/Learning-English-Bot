"""Interactive quiz handlers with multiple-choice questions and instant feedback."""

import random
import logging
from typing import List, Tuple
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.database import Database
from src.formatters import format_quiz_question, format_quiz_feedback
from src.keyboards import get_quiz_options_keyboard, get_quiz_feedback_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def generate_and_send_quiz(chat_id: int, user_id: int, db: Database, bot) -> None:
    """Generate a 4-choice interactive quiz and send it to the user."""
    question_data = await db.get_quiz_question_data(user_id)
    if not question_data:
        await bot.send_message(
            chat_id=chat_id,
            text="⚠️ You need to discover some words first! Tap <b>📖 Today's 5 Words</b> to start.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        return

    target = question_data["target"]
    distractors = question_data["distractors"]

    if len(distractors) < 3:
        await bot.send_message(
            chat_id=chat_id,
            text="⚠️ Not enough words in the vocabulary pool to build a quiz yet.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Determine user's language preference
    user_info = await db.get_or_create_user(user_id)
    pref_lang = user_info.get("preferred_lang", "both")

    # Pick quiz type
    types_pool = ["meaning", "meaning"]  # bias towards English meanings
    if pref_lang in ("both", "ar") and target.get("translation_ar"):
        types_pool.append("translation_ar")
    if pref_lang in ("both", "fr") and target.get("translation_fr"):
        types_pool.append("translation_fr")
    types_pool.append("reverse")

    q_type = random.choice(types_pool)

    # Build choices (choice_id, display_label)
    options: List[Tuple[int, str]] = []
    if q_type == "meaning":
        type_code = "m"
        options.append((target["id"], target["definition"]))
        for d in distractors:
            options.append((d["id"], d["definition"]))
    elif q_type == "translation_ar":
        type_code = "ar"
        options.append((target["id"], target["translation_ar"]))
        for d in distractors:
            options.append((d["id"], d.get("translation_ar") or d["definition"]))
    elif q_type == "translation_fr":
        type_code = "fr"
        options.append((target["id"], target["translation_fr"]))
        for d in distractors:
            options.append((d["id"], d.get("translation_fr") or d["definition"]))
    else:  # reverse
        type_code = "r"
        options.append((target["id"], target["word"].upper()))
        for d in distractors:
            options.append((d["id"], d["word"].upper()))

    # Shuffle choices
    random.shuffle(options)

    prompt_text = format_quiz_question(target, question_type=q_type, lang=pref_lang)
    keyboard = get_quiz_options_keyboard(target["id"], options, q_type=type_code)

    await bot.send_message(
        chat_id=chat_id,
        text=prompt_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quiz command or 'Quick Quiz' menu button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    await generate_and_send_quiz(update.effective_chat.id, user.id, db, context.bot)


async def quiz_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quiz choice button press with instant feedback and streak tracking."""
    query = update.callback_query
    if not query or not query.data:
        return

    parts = query.data.split(":")
    if len(parts) < 4 or parts[0] != "q":
        return

    try:
        target_id = int(parts[1])
        choice_id = int(parts[2])
        type_code = parts[3]
    except ValueError:
        await query.answer("Invalid quiz data.", show_alert=True)
        return

    user = update.effective_user
    db: Database = context.bot_data["db"]

    target_word = await db.get_word_by_id(target_id)
    choice_word = await db.get_word_by_id(choice_id)
    if not target_word or not choice_word:
        await query.answer("Question expired or word not found.", show_alert=True)
        return

    was_correct = (choice_id == target_id)
    type_map = {"m": "meaning", "ar": "translation_ar", "fr": "translation_fr", "r": "reverse"}
    full_type = type_map.get(type_code, "meaning")

    # Record result in database
    result = await db.record_quiz_result(user.id, target_id, full_type, was_correct)

    # Determine display labels
    if type_code == "m":
        user_choice_label = choice_word["definition"]
        correct_choice_label = target_word["definition"]
    elif type_code == "ar":
        user_choice_label = choice_word.get("translation_ar") or choice_word["definition"]
        correct_choice_label = target_word.get("translation_ar") or target_word["definition"]
    elif type_code == "fr":
        user_choice_label = choice_word.get("translation_fr") or choice_word["definition"]
        correct_choice_label = target_word.get("translation_fr") or target_word["definition"]
    else:
        user_choice_label = choice_word["word"].upper()
        correct_choice_label = target_word["word"].upper()

    user_info = await db.get_or_create_user(user.id)
    pref_lang = user_info.get("preferred_lang", "both")

    feedback_text = format_quiz_feedback(
        target_word=target_word,
        was_correct=was_correct,
        user_choice=user_choice_label,
        correct_choice=correct_choice_label,
        streak=result["new_streak"],
        is_now_difficult=result["is_difficult"],
        is_mastered=(result["status"] == "mastered"),
        lang=pref_lang
    )

    alert_popup = "🎉 Correct! Keep it up! 🚀" if was_correct else "❌ Incorrect! Check the explanation below."
    await query.answer(alert_popup)

    feedback_kb = get_quiz_feedback_keyboard(target_id)
    try:
        await query.edit_message_text(
            text=feedback_text,
            parse_mode=ParseMode.HTML,
            reply_markup=feedback_kb
        )
    except Exception as e:
        logger.error(f"Error updating quiz feedback: {e}")


async def quiz_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Next Quiz Question' inline button."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    db: Database = context.bot_data["db"]
    await generate_and_send_quiz(query.message.chat_id, update.effective_user.id, db, context.bot)
