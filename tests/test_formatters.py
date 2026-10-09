"""Tests for HTML message formatting."""

from src.formatters import (
    format_word_card,
    format_daily_lesson_intro,
    format_quiz_question,
    format_quiz_feedback,
    format_progress_report,
    format_progress_bar,
    format_difficult_words_summary
)

SAMPLE_WORD = {
    "id": 1,
    "word": "improve",
    "phonetic": "/ɪmˈpruːv/",
    "part_of_speech": "verb",
    "definition": "To make or become better.",
    "translation_ar": "يُحسِّن",
    "translation_fr": "améliorer",
    "example": "Daily reading will help you improve.",
    "example_translation_ar": "القراءة اليومية ستساعدك على التحسن.",
    "example_translation_fr": "La lecture quotidienne vous aidera à vous améliorer.",
    "level": "A2"
}


def test_format_word_card_both_languages():
    card = format_word_card(SAMPLE_WORD, lang="both", is_difficult=False, index=1)
    assert "IMPROVE" in card
    assert "/ɪmˈpruːv/" in card
    assert "Arabic:" in card
    assert "يُحسِّن" in card
    assert "French:" in card
    assert "améliorer" in card
    assert "Level:" in card


def test_format_word_card_arabic_only():
    card = format_word_card(SAMPLE_WORD, lang="ar", is_difficult=True, index=2)
    assert "Arabic:" in card
    assert "French:" not in card
    assert "(Difficult)" in card


def test_format_word_card_french_only():
    card = format_word_card(SAMPLE_WORD, lang="fr", is_difficult=False)
    assert "French:" in card
    assert "Arabic:" not in card


def test_format_progress_bar():
    bar_50 = format_progress_bar(50.0, total_blocks=10)
    assert "▰▰▰▰▰▱▱▱▱▱" in bar_50
    assert "50.0%" in bar_50

    bar_100 = format_progress_bar(100.0, total_blocks=10)
    assert "▰▰▰▰▰▰▰▰▰▰" in bar_100


def test_format_quiz_question():
    q_meaning = format_quiz_question(SAMPLE_WORD, question_type="meaning")
    assert "What does" in q_meaning
    assert "IMPROVE" in q_meaning

    q_ar = format_quiz_question(SAMPLE_WORD, question_type="translation_ar")
    assert "Arabic translation" in q_ar

    q_fr = format_quiz_question(SAMPLE_WORD, question_type="translation_fr")
    assert "traduction en français" in q_fr


def test_format_quiz_feedback():
    feedback = format_quiz_feedback(
        target_word=SAMPLE_WORD,
        was_correct=True,
        user_choice="To make or become better.",
        correct_choice="To make or become better.",
        streak=5,
        is_now_difficult=False,
        is_mastered=True,
        lang="both"
    )
    assert "EXCELLENT! That's Correct!" in feedback
    assert "MASTERED" in feedback
    assert "5 days" in feedback


def test_format_difficult_words_summary():
    # Empty list
    empty_summary = format_difficult_words_summary([])
    assert "no difficult words" in empty_summary

    # Populated list
    summary = format_difficult_words_summary([SAMPLE_WORD])
    assert "IMPROVE" in summary
    assert "Difficult Words (1 to review)" in summary
