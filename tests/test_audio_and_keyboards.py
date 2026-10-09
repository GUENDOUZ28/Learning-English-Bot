"""Tests for audio caching and keyboard builders."""

from pathlib import Path
from src.audio_service import AudioService
from src.keyboards import (
    get_main_menu_keyboard,
    get_word_actions_keyboard,
    get_quiz_options_keyboard,
    get_quiz_feedback_keyboard,
    get_settings_keyboard
)


def test_audio_sanitize_filename():
    service = AudioService()
    clean = service._sanitize_filename("Persevere!")
    assert clean == "persevere_"

    clean2 = service._sanitize_filename("word-with-hyphen")
    assert clean2 == "word-with-hyphen"


def test_main_menu_keyboard():
    kb = get_main_menu_keyboard()
    assert len(kb.keyboard) == 3
    buttons = [btn.text for row in kb.keyboard for btn in row]
    assert "📖 Today's 5 Words" in buttons
    assert "🎯 Quick Quiz" in buttons
    assert "🔄 Review Words" in buttons
    assert "⚠️ Difficult Words" in buttons
    assert "📊 My Progress" in buttons
    assert "⚙️ Settings" in buttons


def test_quiz_options_keyboard_callback_length():
    """Ensure all callback_data strings stay well below Telegram's 64 byte limit."""
    options = [
        (1, "Option A"),
        (2, "Option B"),
        (3, "Option C"),
        (4, "Option D")
    ]
    kb = get_quiz_options_keyboard(target_id=1, options=options, q_type="m")
    assert len(kb.inline_keyboard) == 4
    for row in kb.inline_keyboard:
        cb = row[0].callback_data
        assert len(cb.encode("utf-8")) <= 64
        assert cb.startswith("q:1:")


def test_settings_keyboard():
    kb = get_settings_keyboard(current_lang="ar", notifications_enabled=True)
    flat_btns = [btn for row in kb.inline_keyboard for btn in row]
    assert any("Arabic Only" in btn.text for btn in flat_btns)
    assert any("Notifications: ON" in btn.text for btn in flat_btns)
