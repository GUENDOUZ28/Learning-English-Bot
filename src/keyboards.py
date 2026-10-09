"""Telegram Reply and Inline keyboards for navigation and interaction."""

from typing import List, Dict, Any, Tuple
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard for fast mobile navigation."""
    keyboard = [
        [KeyboardButton("📖 Today's 5 Words"), KeyboardButton("🎯 Quick Quiz")],
        [KeyboardButton("🔄 Review Words"), KeyboardButton("⚠️ Difficult Words")],
        [KeyboardButton("📊 My Progress"), KeyboardButton("⚙️ Settings")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_word_actions_keyboard(word_id: int, is_difficult: bool = False) -> InlineKeyboardMarkup:
    """Action buttons attached to each word card (Pronunciation & Bookmark)."""
    diff_text = "✅ Remove from Difficult" if is_difficult else "⭐ Mark as Difficult"
    keyboard = [
        [
            InlineKeyboardButton("🔊 Listen Pronunciation", callback_data=f"audio:{word_id}"),
            InlineKeyboardButton(diff_text, callback_data=f"diff:{word_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_options_keyboard(target_id: int, options: List[Tuple[int, str]], q_type: str = "m") -> InlineKeyboardMarkup:
    """
    Build 4 multiple-choice inline buttons.
    options is a list of tuples: (word_id, display_label)
    callback_data format: 'q:<target_id>:<choice_id>:<q_type>' (keeps under 30 bytes)
    """
    buttons = []
    for choice_id, label in options:
        # Trim label if very long
        display_label = label if len(label) <= 50 else label[:47] + "..."
        callback_data = f"q:{target_id}:{choice_id}:{q_type}"
        buttons.append([InlineKeyboardButton(display_label, callback_data=callback_data)])
    return InlineKeyboardMarkup(buttons)


def get_quiz_feedback_keyboard(word_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown after answering a quiz (Next Quiz & Audio)."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Next Quiz Question", callback_data="quiz_next"),
            InlineKeyboardButton("🔊 Pronounce Word", callback_data=f"audio:{word_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(current_lang: str = "both", notifications_enabled: bool = True) -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    # Language indicators
    both_check = "✅ " if current_lang == "both" else ""
    ar_check = "✅ " if current_lang == "ar" else ""
    fr_check = "✅ " if current_lang == "fr" else ""

    notif_btn = "🔔 Notifications: ON" if notifications_enabled else "🔕 Notifications: OFF"

    keyboard = [
        [
            InlineKeyboardButton(f"{both_check}🌍 Arabic & French", callback_data="set_lang:both")
        ],
        [
            InlineKeyboardButton(f"{ar_check}🇸🇦 Arabic Only", callback_data="set_lang:ar"),
            InlineKeyboardButton(f"{fr_check}🇫🇷 French Only", callback_data="set_lang:fr")
        ],
        [
            InlineKeyboardButton(notif_btn, callback_data="toggle_notif")
        ],
        [
            InlineKeyboardButton("⏰ 08:00", callback_data="set_time:08:00"),
            InlineKeyboardButton("⏰ 09:00", callback_data="set_time:09:00"),
            InlineKeyboardButton("⏰ 14:00", callback_data="set_time:14:00"),
            InlineKeyboardButton("⏰ 20:00", callback_data="set_time:20:00")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
