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


def test_audio_manager_no_wait_loops_when_enabled(monkeypatch, tmp_path):
    fake_channel = MagicMock()
    fake_mixer = MagicMock()
    fake_music = MagicMock()
    fake_sound = MagicMock()
    fake_mixer.Sound.return_value = fake_sound
    fake_mixer.find_channel.return_value = fake_channel
    fake_mixer.music = fake_music

    stinger = tmp_path / "stinger.mp3"
    score = tmp_path / "score.mp3"
    stinger.write_bytes(b"\x00" * 16)
    score.write_bytes(b"\x00" * 16)

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
    audio._stinger_path = stinger
    audio._score_path = score

    audio.play_stinger()
    audio.play_score_sfx()
    audio._queue.join()
    assert fake_channel.play.call_count >= 2
    assert not fake_music.wait.called
