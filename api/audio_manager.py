"""Non-blocking audio helper for Hexagon marathon effects."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path

from loguru import logger

from .config import GAMES_ROOT

ENABLE_AUDIO = os.environ.get("ENABLE_AUDIO", "1") == "1"
_AUDIO_DIR = GAMES_ROOT / "audio"

_CMD_START_BGM = "start_bgm"
_CMD_STOP_BGM = "stop_bgm"
_CMD_PLAY_FILE = "play_file"


class AudioManager:
    """Fire-and-forget SFX/BGM — never blocks the game thread."""

    def __init__(self):
        self._mixer = None
        self._music = None
        # Re-read env so tests can toggle after import.
        self._enabled = os.environ.get("ENABLE_AUDIO", "1") == "1"
        self._bgm_path = _AUDIO_DIR / "bgm.mp3"
        self._stinger_path = _AUDIO_DIR / "transition_stinger.mp3"
        self._score_path = _AUDIO_DIR / "prompt.mp3"
        self._hurt_path = _AUDIO_DIR / "broken2.mp3"
        self._countdown_path = _AUDIO_DIR / "countdown.mp3"
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        if self._enabled:
            self._init_mixer()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="hex-audio")
        self._thread.start()

    @property
    def active(self) -> bool:
        return bool(self._enabled and self._mixer is not None)

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

    def _worker(self) -> None:
        while True:
            cmd, payload = self._queue.get()
            try:
                if cmd == _CMD_STOP_BGM:
                    self._stop_bgm_locked()
                elif cmd == _CMD_START_BGM:
                    self._play_file_locked(payload, music=True, loops=-1)
                elif cmd == _CMD_PLAY_FILE:
                    path, loops = payload  # type: ignore[misc]
                    self._play_file_locked(path, music=False, loops=loops)
            except Exception as exc:
                logger.debug(f"Audio worker skip ({cmd}): {exc}")
            finally:
                self._queue.task_done()

    def _stop_bgm_locked(self) -> None:
        if not self._enabled or self._music is None:
            return
        try:
            self._music.stop()
        except Exception:
            pass

    def _play_file_locked(self, path: Path, *, music: bool = False, loops: int = 0) -> None:
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

    def _enqueue(self, cmd: str, payload: object = None) -> None:
        try:
            self._queue.put_nowait((cmd, payload))
        except queue.Full:
            pass

    def start_bgm(self) -> None:
        self._enqueue(_CMD_START_BGM, self._bgm_path)

    def stop_bgm(self) -> None:
        self._enqueue(_CMD_STOP_BGM)

    def play_stinger(self) -> None:
        self._enqueue(_CMD_PLAY_FILE, (self._stinger_path, 0))

    def play_countdown_tick(self) -> None:
        self._enqueue(_CMD_PLAY_FILE, (self._countdown_path, 0))

    def play_score_sfx(self) -> None:
        self._enqueue(_CMD_PLAY_FILE, (self._score_path, 0))

    def play_hurt_sfx(self) -> None:
        self._enqueue(_CMD_PLAY_FILE, (self._hurt_path, 0))
