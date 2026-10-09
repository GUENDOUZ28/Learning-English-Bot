# 🇬🇧 English Vocabulary Learning Telegram Bot

An intelligent, interactive Telegram Bot written in Python that helps learners build an English vocabulary habit every day, practice with interactive quizzes, listen to native voice pronunciation, and reinforce memory through spaced review and streak tracking.

---

## 🌟 Key Features

### 1. 📖 Daily English Words (5 Words / Day)
- **Rich Vocabulary Cards:** Every word includes:
  - Part of speech (e.g. *verb*, *adjective*, *noun*)
  - CEFR level indicator (`A2`, `B1`, `B2`, `C1`)
  - Precise **IPA Phonetic Transcription** (e.g. `/ɪmˈpruːv/`)
  - Clear **English Definition**
  - **Arabic Translation** (🇸🇦 تحسين / يُحسّن)
  - **French Translation** (🇫🇷 améliorer)
  - Authentic **Example Sentence** with contextual Arabic & French translations
- **🔊 Native Voice Pronunciation:** Tap the **Listen Pronunciation** inline button to immediately receive a clear audio pronunciation voice note powered by Text-to-Speech (cached locally on disk).
- **⭐ Difficult Words Bookmark:** Directly tag any unfamiliar word to prioritize it in upcoming review sessions.

### 2. 🎯 Interactive Quizzes
- **Multiple-Choice Questions:** Generates 4-choice questions such as *"What does IMPROVE mean?"*, translation quizzes, and reverse definition challenges.
- **Instant Feedback:** Inline buttons provide real-time validation:
  - ✅ **Correct Answer:** Celebrates success, provides full meaning breakdown, and increments your daily streak.
  - ❌ **Incorrect Answer:** Highlights the mistake, reveals the correct answer with explanation, and automatically queues the word into your **Difficult Words** list for review.
  - **Consecutive Mastery:** Answering a word correctly 3 times advances it to **Mastered** status!

### 3. 📊 Review & Progress Tracking
- **🔥 Daily Streak Counter:** Automatically tracks active days and motivates consistent daily habits.
- **🔄 Spaced Repetition Review:** Revisit words you have previously learned at any time with the `/review` command.
- **⚠️ Difficult Words Drills:** Dedicated review session for vocabulary words you have missed or flagged.
- **📈 Visual Progress Bar:** See your catalog completion percentage, accuracy percentage, and mastery counts at a glance (`▰▰▰▰▰▱▱▱▱▱ 50.0%`).

### 4. ⏰ Automated Daily Lessons
- Built-in background scheduler (powered by `APScheduler` / `JobQueue`) delivers your 5 new words automatically at your preferred time (default: `09:00 AM`).
- Customize reminder time with `/settime HH:MM` (e.g. `/settime 08:30` or `/settime 20:00`).

### 5. ⚙️ User Customization
- Choose translation language preference:
  - 🌍 **Both Arabic & French**
  - 🇸🇦 **Arabic Only**
  - 🇫🇷 **French Only**
- Persistent keyboard menu for one-tap mobile access without typing commands.

---

## 🗂️ Project Architecture

```
telegram-learning-english-bot/
├── data/
│   ├── audio/                 # Cached voice pronunciation .mp3 files
│   └── vocab_bot.db           # SQLite database (auto-created on startup)
├── src/
│   ├── __init__.py
│   ├── config.py              # Environment configuration & constants
│   ├── database.py            # Async SQLite manager (users, words, quizzes, streaks)
│   ├── vocabulary_data.py     # Curated 60+ seed vocabulary entries with translations
│   ├── audio_service.py       # gTTS pronunciation generator with disk cache
│   ├── keyboards.py           # Telegram Reply & Inline keyboards
│   ├── formatters.py          # HTML message styling (cards, quizzes, stats)
│   ├── scheduler.py           # Automated daily lesson delivery
│   ├── bot.py                 # Application builder & handler router
│   └── handlers/
│       ├── start.py           # /start and /help commands
│       ├── daily.py           # Daily 5 words delivery & audio/bookmark callbacks
│       ├── quiz.py            # Quiz generation & instant feedback callbacks
│       ├── review.py          # Review & difficult words drills
│       ├── progress.py        # Progress report & visual progress bars
│       └── settings.py        # Preferences (language, reminder time, alerts)
├── tests/
│   ├── test_database.py       # DB operations, streaks, quiz mechanics tests
│   ├── test_formatters.py     # HTML formatting tests
│   └── test_audio_and_keyboards.py # Audio cacher and keyboard tests
├── .env.example               # Template for configuration
├── pytest.ini                 # Pytest asyncio configuration
├── requirements.txt           # Python dependencies
├── run.py                     # Main application entrypoint
└── README.md                  # Documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- A **Telegram account**

### 2. Get a Telegram Bot Token
1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a name (e.g. `English Vocab Tutor`) and a username ending in `bot` (e.g. `MyDailyEnglishVocabBot`).
4. Copy the API token provided by BotFather (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`).

### 3. Configure `.env`
Create a `.env` file in the project root:
```ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DEFAULT_TRANSLATION_LANG=both
DEFAULT_DAILY_TIME=09:00
DAILY_WORDS_COUNT=5
```

### 4. Install Dependencies
If not already installed:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 5. Initialize the Database & Vocabulary Catalog
You can seed and test the database offline anytime:
```powershell
python run.py --init-db
```
*Output: `Database ready! Catalog contains 60 words.`*

### 6. Run the Bot
```powershell
python run.py
```
Open Telegram, search for your bot username, and send `/start` or tap **Start**!

---

## 📱 Bot Commands & Usage

| Command | Button | Description |
|---|---|---|
| `/start` | — | Welcome message, user registration, and keyboard menu |
| `/daily` | `📖 Today's 5 Words` | Delivers today's 5 vocabulary words with voice audio buttons |
| `/quiz` | `🎯 Quick Quiz` | Generates an interactive multiple-choice question with instant feedback |
| `/review` | `🔄 Review Words` | Revisit previously studied words for memory reinforcement |
| `/difficult` | `⚠️ Difficult Words` | Displays words you found difficult and enables focused practice |
| `/progress` | `📊 My Progress` | Shows daily streak, total words learned, accuracy %, and progress bar |
| `/settings` | `⚙️ Settings` | Switch translation languages (Arabic/French/Both) and reminder time |
| `/settime HH:MM` | — | Set custom daily lesson reminder time (e.g. `/settime 08:30`) |
| `/help` | — | Full command guide and learning tips |

---

## 🧪 Automated Tests

The test suite covers database persistence, streak progression, quiz scoring, mastery thresholds, audio caching, and HTML formatting:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

All **19 tests** pass cleanly with 100% assertions satisfied.

---

## ➕ Adding More Vocabulary Words

To add more vocabulary words to the catalog:
1. Open [`src/vocabulary_data.py`](file:///d:/dossier%20personnel%20Guendouz/develoement/projects/telegram%20learning%20englsih%20bot/src/vocabulary_data.py).
2. Append a dictionary entry to `SEED_WORDS`:
```python
{
    "word": "eloquent",
    "phonetic": "/ˈeləkwənt/",
    "part_of_speech": "adjective",
    "definition": "Fluent or persuasive in speaking or writing.",
    "translation_ar": "بليغ / فصيح",
    "translation_fr": "éloquent",
    "example": "He gave an eloquent speech that moved the entire audience.",
    "example_translation_ar": "ألقى خطاباً بليغاً أثر في الجمهور بأكمله.",
    "example_translation_fr": "Il a prononcé un discours éloquent qui a ému tout le public.",
    "level": "B2"
}
```
3. Run `python run.py --init-db` to update the catalog without losing user history.
