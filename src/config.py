"""Configuration settings for the Vocabulary Learning Telegram Bot."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Database and file storage paths
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "vocab_bot.db")))
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", str(DATA_DIR / "audio")))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# User defaults
DEFAULT_TRANSLATION_LANG = os.getenv("DEFAULT_TRANSLATION_LANG", "both").lower()
if DEFAULT_TRANSLATION_LANG not in ("both", "ar", "fr"):
    DEFAULT_TRANSLATION_LANG = "both"

DEFAULT_DAILY_TIME = os.getenv("DEFAULT_DAILY_TIME", "09:00")
DAILY_WORDS_COUNT = int(os.getenv("DAILY_WORDS_COUNT", "5"))

# Quiz configuration
QUIZ_CHOICES_COUNT = 4
MASTERY_CORRECT_THRESHOLD = 3  # Word is mastered after 3 correct answers
DIFFICULT_WRONG_THRESHOLD = 2  # Word is flagged difficult after 2 wrong answers
