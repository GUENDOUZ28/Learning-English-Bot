"""User settings handlers for language preferences, notification toggles, and schedule times."""

import re
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.database import Database
from src.keyboards import get_settings_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command or 'Settings' button."""
    user = update.effective_user
    if not user:
        return

    db: Database = context.bot_data["db"]
    user_info = await db.get_or_create_user(user.id)

    curr_lang = user_info.get("preferred_lang", "both")
    notif_on = bool(user_info.get("notifications_enabled", 1))
    daily_time = user_info.get("daily_time", "09:00")

    text = (
        "⚙️ <b>Vocabulary Bot Settings</b>\n\n"
        "Customize your learning experience below:\n\n"
        f"• <b>Translations:</b> Choose whether to see Arabic, French, or both.\n"
        f"• <b>Daily Reminder:</b> Currently set to <code>{daily_time}</code>.\n\n"
        "<i>Tap buttons below to change preferences or use <code>/settime HH:MM</code> for custom time:</i>"
    )

    kb = get_settings_keyboard(current_lang=curr_lang, notifications_enabled=notif_on)
    await update.message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings inline button clicks."""
    query = update.callback_query
    if not query or not query.data:
        return

    user = update.effective_user
    db: Database = context.bot_data["db"]
    data = query.data

    if data.startswith("set_lang:"):
        new_lang = data.split(":")[1]
        if new_lang in ("both", "ar", "fr"):
            await db.update_user_settings(user.id, preferred_lang=new_lang)
            await query.answer(f"Language set to: {new_lang.upper()}")

    elif data == "toggle_notif":
        user_info = await db.get_or_create_user(user.id)
        current_state = bool(user_info.get("notifications_enabled", 1))
        new_state = 0 if current_state else 1
        await db.update_user_settings(user.id, notifications_enabled=new_state)
        status_txt = "Notifications turned ON" if new_state else "Notifications turned OFF"
        await query.answer(status_txt)

    elif data.startswith("set_time:"):
        new_time = data.split(":")[1]
        await db.update_user_settings(user.id, daily_time=new_time)
        await query.answer(f"Daily lesson scheduled for {new_time}!")

    # Refresh keyboard
    fresh_user = await db.get_or_create_user(user.id)
    kb = get_settings_keyboard(
        current_lang=fresh_user.get("preferred_lang", "both"),
        notifications_enabled=bool(fresh_user.get("notifications_enabled", 1))
    )
    daily_time = fresh_user.get("daily_time", "09:00")
    text = (
        "⚙️ <b>Vocabulary Bot Settings</b>\n\n"
        "Customize your learning experience below:\n\n"
        f"• <b>Translations:</b> Choose whether to see Arabic, French, or both.\n"
        f"• <b>Daily Reminder:</b> Currently set to <code>{daily_time}</code>.\n\n"
        "<i>Tap buttons below to change preferences or use <code>/settime HH:MM</code> for custom time:</i>"
    )
    try:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        logger.debug(f"Settings message unchanged or edit error: {e}")


async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settime <HH:MM> command."""
    user = update.effective_user
    if not user:
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "⚠️ Please specify a time in 24-hour format (HH:MM).\n"
            "Example: <code>/settime 08:30</code> or <code>/settime 21:00</code>",
            parse_mode=ParseMode.HTML
        )
        return

    time_input = context.args[0].strip()
    match = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", time_input)
    if not match:
        await update.message.reply_text(
            "⚠️ Invalid time format. Please use <b>HH:MM</b> (24-hour format, e.g. <code>08:30</code>).",
            parse_mode=ParseMode.HTML
        )
        return

    db: Database = context.bot_data["db"]
    await db.update_user_settings(user.id, daily_time=time_input)

    await update.message.reply_text(
        f"✅ <b>Daily lesson reminder set to {time_input}!</b>\n"
        "You will receive your 5 vocabulary words automatically at this time every day.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )
