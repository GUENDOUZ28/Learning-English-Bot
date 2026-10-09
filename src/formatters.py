"""HTML formatters for Telegram messages: word cards, quizzes, and progress reports."""

import html
from typing import Dict, Any, List


def escape(text: Any) -> str:
    """HTML escape helper."""
    if text is None:
        return ""
    return html.escape(str(text))


def format_word_card(word_data: Dict[str, Any], lang: str = "both", is_difficult: bool = False, index: int = None) -> str:
    """
    Format a rich vocabulary card for a word in HTML format.
    lang can be 'both', 'ar', or 'fr'.
    """
    word = escape(word_data.get("word", "")).upper()
    phonetic = escape(word_data.get("phonetic", ""))
    pos = escape(word_data.get("part_of_speech", ""))
    definition = escape(word_data.get("definition", ""))
    trans_ar = escape(word_data.get("translation_ar", ""))
    trans_fr = escape(word_data.get("translation_fr", ""))
    example = escape(word_data.get("example", ""))
    ex_ar = escape(word_data.get("example_translation_ar", ""))
    ex_fr = escape(word_data.get("example_translation_fr", ""))
    level = escape(word_data.get("level", "B1"))

    badge = " ⚠️ <i>(Difficult)</i>" if is_difficult else ""
    header_idx = f"#{index} " if index is not None else ""

    lines = [
        f"📖 <b>{header_idx}{word}</b> {phonetic} <i>({pos})</i>{badge}",
        f"🏷️ <b>Level:</b> <code>{level}</code>",
        f"\n💡 <b>Meaning:</b> {definition}\n"
    ]

    # Translations
    if lang in ("both", "ar") and trans_ar:
        lines.append(f"🇸🇦 <b>Arabic:</b> {trans_ar}")
    if lang in ("both", "fr") and trans_fr:
        lines.append(f"🇫🇷 <b>French:</b> {trans_fr}")

    # Example sentence
    if example:
        lines.append(f"\n💬 <b>Example:</b>\n<i>\"{example}\"</i>")
        if lang in ("both", "ar") and ex_ar:
            lines.append(f"↳ 🇸🇦 <i>{ex_ar}</i>")
        if lang in ("both", "fr") and ex_fr:
            lines.append(f"↳ 🇫🇷 <i>{ex_fr}</i>")

    return "\n".join(lines)


def format_daily_lesson_intro(words_count: int, streak: int) -> str:
    """Intro header for daily words lesson."""
    streak_badge = f"🔥 <b>{streak} Day Streak!</b>" if streak > 0 else "🚀 <b>Start your streak today!</b>"
    return (
        f"🌅 <b>Your Daily English Words Lesson</b>\n"
        f"{streak_badge}\n\n"
        f"Here are your <b>{words_count} new words</b> for today. Study their definitions, "
        f"listen to their native pronunciation, and tap <b>Quick Quiz</b> to test your memory!"
    )


def format_quiz_question(target_word: Dict[str, Any], question_type: str = "meaning", lang: str = "both") -> str:
    """Format question prompt."""
    word = escape(target_word.get("word", "")).upper()
    phonetic = escape(target_word.get("phonetic", ""))
    pos = escape(target_word.get("part_of_speech", ""))

    if question_type == "meaning":
        return (
            f"🎯 <b>Vocabulary Quiz</b>\n\n"
            f"What does <b>{word}</b> {phonetic} <i>({pos})</i> mean?\n\n"
            f"<i>Choose the correct definition below:</i>"
        )
    elif question_type == "translation_ar":
        return (
            f"🎯 <b>Translation Quiz (Arabic)</b>\n\n"
            f"What is the Arabic translation of <b>{word}</b> {phonetic}?\n\n"
            f"<i>اختر المعنى الصحيح:</i>"
        )
    elif question_type == "translation_fr":
        return (
            f"🎯 <b>Quiz de Traduction (Français)</b>\n\n"
            f"Quelle est la traduction en français de <b>{word}</b> {phonetic} ?\n\n"
            f"<i>Choisissez la bonne réponse :</i>"
        )
    else:  # reverse
        definition = escape(target_word.get("definition", ""))
        return (
            f"🎯 <b>Reverse Quiz</b>\n\n"
            f"Which word matches this definition?\n"
            f"👉 <i>\"{definition}\"</i>\n\n"
            f"<i>Choose the correct word:</i>"
        )


def format_quiz_feedback(
    target_word: Dict[str, Any],
    was_correct: bool,
    user_choice: str,
    correct_choice: str,
    streak: int,
    is_now_difficult: bool,
    is_mastered: bool,
    lang: str = "both"
) -> str:
    """Rich feedback after answering a quiz question."""
    word = escape(target_word.get("word", "")).upper()
    phonetic = escape(target_word.get("phonetic", ""))
    definition = escape(target_word.get("definition", ""))
    trans_ar = escape(target_word.get("translation_ar", ""))
    trans_fr = escape(target_word.get("translation_fr", ""))
    example = escape(target_word.get("example", ""))

    lines = []
    if was_correct:
        lines.append("🎉 <b>EXCELLENT! That's Correct!</b> ✅")
    else:
        lines.append("❌ <b>Oops! Not quite right.</b>")
        lines.append(f"Your answer: <s>{escape(user_choice)}</s>")
        lines.append(f"Correct answer: <b>{escape(correct_choice)}</b>")

    lines.append("")
    lines.append(f"📌 <b>{word}</b> {phonetic}")
    lines.append(f"💡 <b>Meaning:</b> {definition}")

    if lang in ("both", "ar") and trans_ar:
        lines.append(f"🇸🇦 <b>Arabic:</b> {trans_ar}")
    if lang in ("both", "fr") and trans_fr:
        lines.append(f"🇫🇷 <b>French:</b> {trans_fr}")

    if example:
        lines.append(f"💬 <i>\"{example}\"</i>")

    lines.append("")
    if is_mastered:
        lines.append("🌟 <b>Congratulations! You've MASTERED this word!</b> 🎓")
    elif is_now_difficult:
        lines.append("⚠️ <b>This word has been added to your Difficult Words review list.</b>")

    lines.append(f"🔥 <b>Current Streak:</b> {streak} day{'s' if streak != 1 else ''}!")

    return "\n".join(lines)


def format_progress_bar(percentage: float, total_blocks: int = 10) -> str:
    """Render a visual ASCII progress bar, e.g. ▰▰▰▰▰▱▱▱▱▱ 50%."""
    filled = int(round((percentage / 100.0) * total_blocks))
    filled = max(0, min(total_blocks, filled))
    empty = total_blocks - filled
    bar = "▰" * filled + "▱" * empty
    return f"{bar} {percentage:.1f}%"


def format_progress_report(stats: Dict[str, Any], first_name: str = "") -> str:
    """Format full statistics and progress summary."""
    streak = stats.get("streak", 0)
    total_cat = stats.get("total_catalog", 0)
    total_learned = stats.get("total_learned", 0)
    mastered = stats.get("mastered_count", 0)
    learning = stats.get("learning_count", 0)
    difficult = stats.get("difficult_count", 0)
    quizzes = stats.get("total_quizzes", 0)
    correct = stats.get("correct_quizzes", 0)
    accuracy = stats.get("accuracy", 0.0)
    lang = stats.get("preferred_lang", "both")
    daily_time = stats.get("daily_time", "09:00")
    notif = "🔔 Enabled" if stats.get("notifications_enabled", True) else "🔕 Disabled"

    catalog_pct = (total_learned / total_cat * 100) if total_cat > 0 else 0.0
    bar = format_progress_bar(catalog_pct)

    lang_labels = {
        "both": "🌍 Arabic & French",
        "ar": "🇸🇦 Arabic",
        "fr": "🇫🇷 French"
    }
    lang_name = lang_labels.get(lang, "🌍 Arabic & French")

    name_str = f" for <b>{escape(first_name)}</b>" if first_name else ""

    return (
        f"📊 <b>Vocabulary Learning Progress{name_str}</b>\n\n"
        f"🔥 <b>Daily Streak:</b> {streak} day{'s' if streak != 1 else ''}\n\n"
        f"📚 <b>Catalog Progress:</b> {total_learned} / {total_cat} words\n"
        f"<code>{bar}</code>\n\n"
        f"• 🌟 <b>Mastered:</b> {mastered} words\n"
        f"• 📖 <b>Currently Learning:</b> {learning} words\n"
        f"• ⚠️ <b>Difficult (Need Review):</b> {difficult} words\n\n"
        f"🎯 <b>Quiz Performance:</b>\n"
        f"• Quizzes Taken: <b>{quizzes}</b>\n"
        f"• Correct Answers: <b>{correct}</b>\n"
        f"• Accuracy: <b>{accuracy}%</b>\n\n"
        f"⚙️ <b>Settings:</b>\n"
        f"• Translations: {lang_name}\n"
        f"• Daily Lesson Time: <code>{daily_time}</code> ({notif})"
    )


def format_difficult_words_summary(words: List[Dict[str, Any]]) -> str:
    """Format list of difficult words."""
    if not words:
        return (
            "🎉 <b>Awesome! You have no difficult words right now!</b>\n\n"
            "Keep practicing with <b>Today's Words</b> and <b>Quick Quiz</b>. "
            "Any words you struggle with will appear here automatically."
        )

    lines = [
        f"⚠️ <b>Difficult Words ({len(words)} to review)</b>\n",
        "Here are vocabulary words that need extra attention:\n"
    ]

    for i, w in enumerate(words, 1):
        word_name = escape(w.get("word", "")).upper()
        phonetic = escape(w.get("phonetic", ""))
        pos = escape(w.get("part_of_speech", ""))
        definition = escape(w.get("definition", ""))
        wrong = w.get("wrong_count", 0)
        lines.append(
            f"<b>{i}. {word_name}</b> {phonetic} <i>({pos})</i> (❌ missed {wrong}x)\n"
            f"   ↳ {definition}\n"
        )

    lines.append("<i>Tip: Use '🎯 Quick Quiz' to practice and master them!</i>")
    return "\n".join(lines)
