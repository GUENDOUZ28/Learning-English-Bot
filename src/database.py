"""Async SQLite database manager for vocabulary learning bot."""

import json
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
import aiosqlite

from src.config import DATABASE_PATH, MASTERY_CORRECT_THRESHOLD, DIFFICULT_WRONG_THRESHOLD
from src.vocabulary_data import SEED_WORDS


class Database:
    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Async context manager for SQLite database connection."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON;")
            yield db

    async def init_db(self, seed_words: Optional[List[Dict[str, Any]]] = None) -> None:
        """Create database tables and seed initial vocabulary."""
        async with self.get_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    preferred_lang TEXT DEFAULT 'both',
                    daily_time TEXT DEFAULT '09:00',
                    notifications_enabled INTEGER DEFAULT 1,
                    streak INTEGER DEFAULT 0,
                    last_active_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    phonetic TEXT,
                    part_of_speech TEXT,
                    definition TEXT NOT NULL,
                    translation_ar TEXT,
                    translation_fr TEXT,
                    example TEXT,
                    example_translation_ar TEXT,
                    example_translation_fr TEXT,
                    level TEXT DEFAULT 'B1',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_words (
                    user_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'learning',
                    is_difficult INTEGER DEFAULT 0,
                    times_reviewed INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0,
                    wrong_count INTEGER DEFAULT 0,
                    last_reviewed_at TIMESTAMP,
                    PRIMARY KEY (user_id, word_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    delivery_date TEXT NOT NULL,
                    word_ids TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS quiz_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    question_type TEXT NOT NULL,
                    was_correct INTEGER NOT NULL,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
                );
            """)

            await db.commit()

            # Seed vocabulary
            words_to_seed = seed_words if seed_words is not None else SEED_WORDS
            for w in words_to_seed:
                await db.execute("""
                    INSERT OR IGNORE INTO words (
                        word, phonetic, part_of_speech, definition,
                        translation_ar, translation_fr, example,
                        example_translation_ar, example_translation_fr, level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    w["word"].strip().lower(),
                    w.get("phonetic", ""),
                    w.get("part_of_speech", ""),
                    w.get("definition", ""),
                    w.get("translation_ar", ""),
                    w.get("translation_fr", ""),
                    w.get("example", ""),
                    w.get("example_translation_ar", ""),
                    w.get("example_translation_fr", ""),
                    w.get("level", "B1")
                ))

            await db.commit()

    # ---------------------------------------------------------
    # USER OPERATIONS
    # ---------------------------------------------------------

    async def get_or_create_user(self, user_id: int, first_name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
        """Fetch or register a user."""
        async with self.get_connection() as db:
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)

            # Insert new user
            await db.execute("""
                INSERT INTO users (user_id, first_name, username)
                VALUES (?, ?, ?)
            """, (user_id, first_name or "", username or ""))
            await db.commit()

            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            new_row = await cursor.fetchone()
            return dict(new_row)

    async def update_user_settings(self, user_id: int, **kwargs) -> None:
        """Update user preferences (preferred_lang, daily_time, notifications_enabled)."""
        allowed = {"preferred_lang", "daily_time", "notifications_enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())
        values.append(user_id)

        async with self.get_connection() as db:
            await db.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            await db.commit()

    async def update_user_streak(self, user_id: int) -> Tuple[int, bool]:
        """
        Update streak for user activity today.
        Returns: (current_streak, increased_boolean)
        """
        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        async with self.get_connection() as db:
            cursor = await db.execute("SELECT streak, last_active_date FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if not row:
                return (0, False)

            streak = row["streak"]
            last_active = row["last_active_date"]

            if last_active == today_str:
                return (streak, False)

            if last_active == yesterday_str:
                streak += 1
            else:
                streak = 1

            await db.execute("UPDATE users SET streak = ?, last_active_date = ? WHERE user_id = ?",
                             (streak, today_str, user_id))
            await db.commit()
            return (streak, True)

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Aggregate learning statistics for a given user."""
        async with self.get_connection() as db:
            # User basic info
            u_cur = await db.execute("SELECT streak, preferred_lang, daily_time, notifications_enabled FROM users WHERE user_id = ?", (user_id,))
            u_row = await u_cur.fetchone()
            user_data = dict(u_row) if u_row else {
                "streak": 0, "preferred_lang": "both", "daily_time": "09:00", "notifications_enabled": 1
            }

            # Catalog total
            cat_cur = await db.execute("SELECT COUNT(*) as count FROM words")
            total_catalog = (await cat_cur.fetchone())["count"]

            # User words breakdown
            uw_cur = await db.execute("""
                SELECT
                    COUNT(*) as total_learned,
                    SUM(CASE WHEN status = 'mastered' THEN 1 ELSE 0 END) as mastered_count,
                    SUM(CASE WHEN status = 'learning' THEN 1 ELSE 0 END) as learning_count,
                    SUM(CASE WHEN is_difficult = 1 THEN 1 ELSE 0 END) as difficult_count
                FROM user_words
                WHERE user_id = ?
            """, (user_id,))
            uw_row = await uw_cur.fetchone()

            total_learned = uw_row["total_learned"] or 0
            mastered_count = uw_row["mastered_count"] or 0
            learning_count = uw_row["learning_count"] or 0
            difficult_count = uw_row["difficult_count"] or 0

            # Quiz history breakdown
            qh_cur = await db.execute("""
                SELECT
                    COUNT(*) as total_quizzes,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_quizzes
                FROM quiz_history
                WHERE user_id = ?
            """, (user_id,))
            qh_row = await qh_cur.fetchone()

            total_quizzes = qh_row["total_quizzes"] or 0
            correct_quizzes = qh_row["correct_quizzes"] or 0
            accuracy = round((correct_quizzes / total_quizzes * 100), 1) if total_quizzes > 0 else 0.0

            return {
                "streak": user_data["streak"],
                "preferred_lang": user_data["preferred_lang"],
                "daily_time": user_data["daily_time"],
                "notifications_enabled": bool(user_data["notifications_enabled"]),
                "total_catalog": total_catalog,
                "total_learned": total_learned,
                "mastered_count": mastered_count,
                "learning_count": learning_count,
                "difficult_count": difficult_count,
                "total_quizzes": total_quizzes,
                "correct_quizzes": correct_quizzes,
                "accuracy": accuracy
            }

    # ---------------------------------------------------------
    # DAILY LESSON & WORD OPERATIONS
    # ---------------------------------------------------------

    async def get_word_by_id(self, word_id: int) -> Optional[Dict[str, Any]]:
        async with self.get_connection() as db:
            cur = await db.execute("SELECT * FROM words WHERE id = ?", (word_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_daily_words_for_user(self, user_id: int, count: int = 5, force_new: bool = False) -> List[Dict[str, Any]]:
        """
        Get 5 words for today.
        If already delivered today and force_new=False, returns the exact words sent earlier today.
        Otherwise selects unseen words, records delivery, and marks them in user_words.
        """
        today_str = date.today().isoformat()

        async with self.get_connection() as db:
            if not force_new:
                # Check existing delivery today
                cur = await db.execute("""
                    SELECT word_ids FROM daily_deliveries
                    WHERE user_id = ? AND delivery_date = ?
                    ORDER BY id DESC LIMIT 1
                """, (user_id, today_str))
                deliv_row = await cur.fetchone()
                if deliv_row:
                    word_ids = json.loads(deliv_row["word_ids"])
                    if word_ids:
                        placeholders = ",".join("?" for _ in word_ids)
                        w_cur = await db.execute(f"SELECT * FROM words WHERE id IN ({placeholders})", word_ids)
                        rows = await w_cur.fetchall()
                        # Sort back to original order
                        row_dict = {r["id"]: dict(r) for r in rows}
                        return [row_dict[wid] for wid in word_ids if wid in row_dict]

            # Find unseen words first
            cur = await db.execute("""
                SELECT w.* FROM words w
                LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = ?
                WHERE uw.word_id IS NULL
                ORDER BY w.id ASC
                LIMIT ?
            """, (user_id, count))
            selected = [dict(r) for r in await cur.fetchall()]

            # If fewer than 'count' unseen words exist, top up with words with lowest review count
            if len(selected) < count:
                needed = count - len(selected)
                existing_ids = [w["id"] for w in selected]
                exclude_clause = f"AND w.id NOT IN ({','.join('?' for _ in existing_ids)})" if existing_ids else ""
                topup_cur = await db.execute(f"""
                    SELECT w.* FROM words w
                    JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = ?
                    WHERE 1=1 {exclude_clause}
                    ORDER BY uw.times_reviewed ASC, uw.last_reviewed_at ASC
                    LIMIT ?
                """, [user_id] + existing_ids + [needed])
                topup_rows = [dict(r) for r in await topup_cur.fetchall()]
                selected.extend(topup_rows)

            if not selected:
                # Fallback to any random words
                cur = await db.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT ?", (count,))
                selected = [dict(r) for r in await cur.fetchall()]

            # Record in user_words and daily_deliveries
            word_ids = [w["id"] for w in selected]
            now_iso = datetime.now(timezone.utc).isoformat()

            for wid in word_ids:
                await db.execute("""
                    INSERT INTO user_words (user_id, word_id, status, times_reviewed, last_reviewed_at)
                    VALUES (?, ?, 'learning', 1, ?)
                    ON CONFLICT(user_id, word_id) DO UPDATE SET
                        times_reviewed = times_reviewed + 1,
                        last_reviewed_at = excluded.last_reviewed_at
                """, (user_id, wid, now_iso))

            await db.execute("""
                INSERT INTO daily_deliveries (user_id, delivery_date, word_ids)
                VALUES (?, ?, ?)
            """, (user_id, today_str, json.dumps(word_ids)))

            await db.commit()

        # Update streak
        await self.update_user_streak(user_id)
        return selected

    async def toggle_word_difficult(self, user_id: int, word_id: int, set_difficult: Optional[bool] = None) -> bool:
        """Toggle or set word difficult status. Returns new status (True/False)."""
        async with self.get_connection() as db:
            cur = await db.execute("SELECT is_difficult FROM user_words WHERE user_id = ? AND word_id = ?", (user_id, word_id))
            row = await cur.fetchone()

            if row is None:
                # Add word to user_words first
                new_status = True if set_difficult is None else set_difficult
                await db.execute("""
                    INSERT INTO user_words (user_id, word_id, is_difficult, status)
                    VALUES (?, ?, ?, 'learning')
                """, (user_id, word_id, 1 if new_status else 0))
            else:
                current = bool(row["is_difficult"])
                new_status = not current if set_difficult is None else set_difficult
                await db.execute("""
                    UPDATE user_words SET is_difficult = ? WHERE user_id = ? AND word_id = ?
                """, (1 if new_status else 0, user_id, word_id))

            await db.commit()
            return new_status

    async def is_word_difficult(self, user_id: int, word_id: int) -> bool:
        """Check if a word is marked difficult by the user."""
        async with self.get_connection() as db:
            cur = await db.execute("SELECT is_difficult FROM user_words WHERE user_id = ? AND word_id = ?", (user_id, word_id))
            row = await cur.fetchone()
            return bool(row["is_difficult"]) if row else False

    async def get_difficult_words(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch words flagged as difficult for the user."""
        async with self.get_connection() as db:
            cur = await db.execute("""
                SELECT w.*, uw.correct_count, uw.wrong_count, uw.times_reviewed
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = ? AND uw.is_difficult = 1
                ORDER BY uw.wrong_count DESC, uw.last_reviewed_at ASC
                LIMIT ?
            """, (user_id, limit))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_review_words(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch previously delivered words that need review."""
        async with self.get_connection() as db:
            cur = await db.execute("""
                SELECT w.*, uw.status, uw.is_difficult, uw.correct_count, uw.wrong_count
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = ?
                ORDER BY uw.is_difficult DESC, uw.last_reviewed_at ASC
                LIMIT ?
            """, (user_id, limit))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # ---------------------------------------------------------
    # QUIZ GENERATION & ANSWER RECORDING
    # ---------------------------------------------------------

    async def get_quiz_question_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Selects a target word for quiz:
        1. Difficult words (50% bias if available)
        2. Words in learning
        3. Random word from catalog
        Fetches 3 distinct distractors from words table.
        """
        async with self.get_connection() as db:
            target_word = None

            # Check difficult words
            cur = await db.execute("""
                SELECT w.* FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = ? AND uw.is_difficult = 1
                ORDER BY RANDOM() LIMIT 1
            """, (user_id,))
            target_word = await cur.fetchone()

            # Otherwise learning words
            if not target_word:
                cur = await db.execute("""
                    SELECT w.* FROM words w
                    JOIN user_words uw ON w.id = uw.word_id
                    WHERE uw.user_id = ? AND uw.status = 'learning'
                    ORDER BY RANDOM() LIMIT 1
                """, (user_id,))
                target_word = await cur.fetchone()

            # Otherwise any word in catalog
            if not target_word:
                cur = await db.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
                target_word = await cur.fetchone()

            if not target_word:
                return None

            target = dict(target_word)

            # Get 3 distractors
            dist_cur = await db.execute("""
                SELECT * FROM words
                WHERE id != ?
                ORDER BY RANDOM() LIMIT 3
            """, (target["id"],))
            distractors = [dict(r) for r in await dist_cur.fetchall()]

            return {
                "target": target,
                "distractors": distractors
            }

    async def record_quiz_result(self, user_id: int, word_id: int, question_type: str, was_correct: bool) -> Dict[str, Any]:
        """
        Record quiz response and update mastery / difficulty status.
        Returns: {
            "was_correct": bool,
            "status": "learning" | "mastered",
            "is_difficult": bool,
            "new_streak": int
        }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        is_corr_int = 1 if was_correct else 0

        async with self.get_connection() as db:
            # Insert history
            await db.execute("""
                INSERT INTO quiz_history (user_id, word_id, question_type, was_correct)
                VALUES (?, ?, ?, ?)
            """, (user_id, word_id, question_type, is_corr_int))

            # Fetch or init user_word
            cur = await db.execute("SELECT * FROM user_words WHERE user_id = ? AND word_id = ?", (user_id, word_id))
            uw_row = await cur.fetchone()

            if not uw_row:
                correct_count = 1 if was_correct else 0
                wrong_count = 0 if was_correct else 1
                status = "mastered" if correct_count >= MASTERY_CORRECT_THRESHOLD else "learning"
                is_difficult = 1 if wrong_count >= DIFFICULT_WRONG_THRESHOLD else 0

                await db.execute("""
                    INSERT INTO user_words (
                        user_id, word_id, status, is_difficult,
                        times_reviewed, correct_count, wrong_count, last_reviewed_at
                    ) VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """, (user_id, word_id, status, is_difficult, correct_count, wrong_count, now_iso))
            else:
                correct_count = uw_row["correct_count"] + (1 if was_correct else 0)
                wrong_count = uw_row["wrong_count"] + (0 if was_correct else 1)
                is_diff = uw_row["is_difficult"]

                if was_correct:
                    if correct_count >= MASTERY_CORRECT_THRESHOLD:
                        status = "mastered"
                        is_diff = 0
                    else:
                        status = uw_row["status"]
                else:
                    status = "learning"
                    if wrong_count >= DIFFICULT_WRONG_THRESHOLD:
                        is_diff = 1

                await db.execute("""
                    UPDATE user_words SET
                        times_reviewed = times_reviewed + 1,
                        correct_count = ?,
                        wrong_count = ?,
                        status = ?,
                        is_difficult = ?,
                        last_reviewed_at = ?
                    WHERE user_id = ? AND word_id = ?
                """, (correct_count, wrong_count, status, is_diff, now_iso, user_id, word_id))
                is_difficult = is_diff

            await db.commit()

        # Update streak
        streak, _ = await self.update_user_streak(user_id)

        return {
            "was_correct": was_correct,
            "status": status,
            "is_difficult": bool(is_difficult),
            "new_streak": streak
        }

    # ---------------------------------------------------------
    # AUTOMATED SCHEDULING
    # ---------------------------------------------------------

    async def get_users_for_daily_notification(self, current_time_str: str) -> List[int]:
        """Find user IDs scheduled for daily notification at given HH:MM."""
        async with self.get_connection() as db:
            cur = await db.execute("""
                SELECT user_id FROM users
                WHERE notifications_enabled = 1 AND daily_time = ?
            """, (current_time_str,))
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]

    async def get_all_active_users(self) -> List[int]:
        """Fetch all user IDs."""
        async with self.get_connection() as db:
            cur = await db.execute("SELECT user_id FROM users")
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]
