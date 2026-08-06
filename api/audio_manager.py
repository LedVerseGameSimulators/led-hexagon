"""Non-blocking audio helper for Hexagon marathon effects."""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger

from .config import GAMES_ROOT

ENABLE_AUDIO = os.environ.get("ENABLE_AUDIO", "0") == "1"
_AUDIO_DIR = GAMES_ROOT / "audio"


class AudioManager:
    """Fire-and-forget SFX/BGM — never blocks the game thread."""

    def __init__(self):
        self._mixer = None
        self._music = None
        self._enabled = ENABLE_AUDIO
        self._bgm_path = _AUDIO_DIR / "bgm.mp3"
        self._stinger_path = _AUDIO_DIR / "transition_stinger.mp3"
        self._score_path = _AUDIO_DIR / "prompt.mp3"
        self._hurt_path = _AUDIO_DIR / "broken2.mp3"
        self._countdown_path = _AUDIO_DIR / "countdown.mp3"
        if self._enabled:
            self._init_mixer()

    @property
    def active(self) -> bool:
        return self._enabled

    def _init_mixer(self) -> None:
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer = pygame.mixer
            self._music = pygame.mixer.music
        except Exception as exc:
            logger.warning(f"AudioManager disabled: {exc}")
            self._enabled = False

    def _play_file(self, path: Path, *, music: bool = False, loops: int = 0) -> None:
        if not self._enabled or not path.is_file():
            return
        try:
            if music:
                self._music.load(str(path))
                self._music.play(loops)
            else:
                sound = self._mixer.Sound(str(path))
                sound.play()
        except Exception as exc:
            logger.debug(f"Audio play skipped ({path.name}): {exc}")

    def start_bgm(self) -> None:
        self._play_file(self._bgm_path, music=True, loops=-1)

    def stop_bgm(self) -> None:
        if not self._enabled:
            return
        try:
            self._music.stop()
        except Exception:
            pass

    def play_stinger(self) -> None:
        self._play_file(self._stinger_path)

    def play_countdown_tick(self) -> None:
        self._play_file(self._countdown_path)

    def play_score_sfx(self) -> None:
        self._play_file(self._score_path)

    def play_hurt_sfx(self) -> None:
        self._play_file(self._hurt_path)
