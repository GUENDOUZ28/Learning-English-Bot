"""Unit and integration tests for database operations."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import date, timedelta

from src.database import Database
from src.vocabulary_data import SEED_WORDS

import pytest_asyncio


@pytest_asyncio.fixture
async def temp_db():
    """Create a temporary SQLite database for isolated tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = Database(db_path=db_path)
    await db.init_db(seed_words=SEED_WORDS[:15])  # Use subset of 15 words for fast test
    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_init_db(temp_db):
    """Verify tables creation and seeding."""
    stats = await temp_db.get_user_stats(user_id=123)
    assert stats["total_catalog"] == 15
    assert stats["total_learned"] == 0


@pytest.mark.asyncio
async def test_get_or_create_user(temp_db):
    """Test user creation and fetching."""
    user = await temp_db.get_or_create_user(user_id=101, first_name="Alice", username="alice_dev")
    assert user["user_id"] == 101
    assert user["first_name"] == "Alice"
    assert user["preferred_lang"] == "both"
    assert user["streak"] == 0

    # Fetching existing user should return same record
    user2 = await temp_db.get_or_create_user(user_id=101, first_name="AliceUpdated")
    assert user2["user_id"] == 101
    assert user2["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_update_user_settings(temp_db):
    """Test updating language preferences and daily reminder times."""
    await temp_db.get_or_create_user(user_id=202)
    await temp_db.update_user_settings(user_id=202, preferred_lang="ar", daily_time="08:30", notifications_enabled=0)

    user = await temp_db.get_or_create_user(user_id=202)
    assert user["preferred_lang"] == "ar"
    assert user["daily_time"] == "08:30"
    assert user["notifications_enabled"] == 0


@pytest.mark.asyncio
async def test_daily_words_delivery(temp_db):
    """Test delivering 5 daily words and ensuring idempotency on the same day."""
    user_id = 303
    await temp_db.get_or_create_user(user_id)

    # First call: delivers 5 words
    words_day1 = await temp_db.get_daily_words_for_user(user_id, count=5)
    assert len(words_day1) == 5

    # Second call today: should return the exact same 5 words
    words_repeat = await temp_db.get_daily_words_for_user(user_id, count=5)
    assert [w["id"] for w in words_day1] == [w["id"] for w in words_repeat]

    # Check that user_words recorded them as 'learning'
    stats = await temp_db.get_user_stats(user_id)
    assert stats["total_learned"] == 5
    assert stats["learning_count"] == 5
    assert stats["mastered_count"] == 0


@pytest.mark.asyncio
async def test_streak_calculation(temp_db):
    """Test streak incrementation and reset logic."""
    user_id = 404
    await temp_db.get_or_create_user(user_id)

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    two_days_ago = (date.today() - timedelta(days=2)).isoformat()

    # Activity today: streak becomes 1
    streak, inc = await temp_db.update_user_streak(user_id)
    assert streak == 1
    assert inc is True

    # Same day activity: streak unchanged
    streak, inc = await temp_db.update_user_streak(user_id)
    assert streak == 1
    assert inc is False

    # Simulate user was active yesterday with streak 3
    async with temp_db.get_connection() as db:
        await db.execute("UPDATE users SET streak = 3, last_active_date = ? WHERE user_id = ?", (yesterday, user_id))
        await db.commit()

    # Now active today: streak should become 4
    streak, inc = await temp_db.update_user_streak(user_id)
    assert streak == 4
    assert inc is True

    # Simulate gap: last active 2 days ago with streak 4
    async with temp_db.get_connection() as db:
        await db.execute("UPDATE users SET streak = 4, last_active_date = ? WHERE user_id = ?", (two_days_ago, user_id))
        await db.commit()

    # Active today after gap: streak resets to 1
    streak, inc = await temp_db.update_user_streak(user_id)
    assert streak == 1
    assert inc is True


@pytest.mark.asyncio
async def test_difficult_words_toggle(temp_db):
    """Test bookmarking / unmarking difficult words."""
    user_id = 505
    await temp_db.get_or_create_user(user_id)

    # Word 1
    is_diff = await temp_db.toggle_word_difficult(user_id, word_id=1)
    assert is_diff is True
    assert await temp_db.is_word_difficult(user_id, word_id=1) is True

    diff_list = await temp_db.get_difficult_words(user_id)
    assert len(diff_list) == 1
    assert diff_list[0]["id"] == 1

    # Toggle off
    is_diff = await temp_db.toggle_word_difficult(user_id, word_id=1)
    assert is_diff is False
    assert await temp_db.is_word_difficult(user_id, word_id=1) is False


@pytest.mark.asyncio
async def test_quiz_and_mastery(temp_db):
    """Test quiz question building, answer recording, mastery threshold, and accuracy."""
    user_id = 606
    await temp_db.get_or_create_user(user_id)

    # Generate quiz question
    q_data = await temp_db.get_quiz_question_data(user_id)
    assert q_data is not None
    assert "target" in q_data
    assert len(q_data["distractors"]) == 3

    target_id = q_data["target"]["id"]

    # Answer correctly 3 times -> word should reach 'mastered' status
    res1 = await temp_db.record_quiz_result(user_id, target_id, "meaning", was_correct=True)
    assert res1["was_correct"] is True
    assert res1["status"] == "learning"

    res2 = await temp_db.record_quiz_result(user_id, target_id, "meaning", was_correct=True)
    assert res2["status"] == "learning"

    res3 = await temp_db.record_quiz_result(user_id, target_id, "meaning", was_correct=True)
    assert res3["status"] == "mastered"

    # Check stats
    stats = await temp_db.get_user_stats(user_id)
    assert stats["total_quizzes"] == 3
    assert stats["correct_quizzes"] == 3
    assert stats["accuracy"] == 100.0
    assert stats["mastered_count"] == 1


@pytest.mark.asyncio
async def test_quiz_wrong_answers_flag_difficult(temp_db):
    """Test that answering wrongly twice automatically flags a word as difficult."""
    user_id = 707
    await temp_db.get_or_create_user(user_id)
    word_id = 2

    # Wrong answer 1
    res1 = await temp_db.record_quiz_result(user_id, word_id, "meaning", was_correct=False)
    assert res1["is_difficult"] is False

    # Wrong answer 2 -> threshold reached, marked difficult
    res2 = await temp_db.record_quiz_result(user_id, word_id, "meaning", was_correct=False)
    assert res2["is_difficult"] is True

    diff_list = await temp_db.get_difficult_words(user_id)
    assert any(w["id"] == word_id for w in diff_list)
