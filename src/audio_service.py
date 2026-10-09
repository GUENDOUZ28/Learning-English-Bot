"""Audio pronunciation service using gTTS with disk caching."""

import asyncio
import re
import logging
from pathlib import Path
from typing import Optional
from gtts import gTTS

from src.config import AUDIO_DIR

logger = logging.getLogger(__name__)


class AudioService:
    def __init__(self, cache_dir: Path = AUDIO_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        """Create safe filename from word or phrase."""
        clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', text.strip().lower())
        return clean[:50]

    def _generate_audio_sync(self, text: str, output_path: Path, lang: str = "en") -> bool:
        """Synchronous generation of audio using gTTS."""
        try:
            tts = gTTS(text=text, lang=lang, tld="com", slow=False)
            tts.save(str(output_path))
            return True
        except Exception as e:
            logger.warning(f"Could not generate TTS audio for '{text}': {e}")
            return False

    async def get_word_pronunciation_path(self, word: str) -> Optional[Path]:
        """
        Get existing cached audio file path or generate a new one asynchronously.
        Returns Path to the .mp3 file, or None if generation failed.
        """
        safe_name = self._sanitize_filename(word)
        file_path = self.cache_dir / f"{safe_name}.mp3"

        if file_path.exists() and file_path.stat().st_size > 0:
            return file_path

        # Generate in thread pool to prevent blocking asyncio loop
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            None,
            self._generate_audio_sync,
            word,
            file_path,
            "en"
        )

        return file_path if (success and file_path.exists()) else None


audio_service = AudioService()
