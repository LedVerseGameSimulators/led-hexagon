"""T9: AudioManager is non-blocking (no game-thread waits)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from api.audio_manager import AudioManager


def test_audio_manager_methods_return_immediately(monkeypatch):
    monkeypatch.setenv("ENABLE_AUDIO", "0")
    audio = AudioManager()
    start = time.perf_counter()
    audio.start_bgm()
    audio.play_stinger()
    audio.play_countdown_tick()
    audio.play_score_sfx()
    audio.play_hurt_sfx()
    audio.stop_bgm()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.05
    assert audio.active is False


def test_audio_manager_no_wait_loops_when_enabled(monkeypatch):
    fake_mixer = MagicMock()
    fake_music = MagicMock()
    fake_sound = MagicMock()
    fake_mixer.Sound.return_value = fake_sound
    fake_mixer.music = fake_music

    monkeypatch.setenv("ENABLE_AUDIO", "1")
    monkeypatch.setitem(
        __import__("sys").modules,
        "pygame",
        MagicMock(mixer=fake_mixer, init=MagicMock()),
    )

    audio = AudioManager()
    audio._enabled = True
    audio._mixer = fake_mixer
    audio._music = fake_music
    audio._stinger_path = __import__("pathlib").Path("/tmp/stinger.mp3")
    audio._score_path = __import__("pathlib").Path("/tmp/score.mp3")

    monkeypatch.setattr(__import__("pathlib").Path, "is_file", lambda self: True)

    audio.play_stinger()
    audio.play_score_sfx()
    fake_mixer.Sound.return_value.play.assert_called()
    assert not fake_music.wait.called
