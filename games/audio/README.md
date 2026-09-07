# Hexagon / Arena audio (effects contract)

Runtime (`api/audio_manager.py`) uses legacy names; venue pack mapped onto them:

| Runtime file | Role | Notes |
|--------------|------|-------|
| `bgm.mp3` | BGM | From Battle Arena pack (TRON End of Line) |
| `prompt.mp3` | +score | From pack positive |
| `broken2.mp3` | −score | From pack negative |
| `countdown.mp3` | tick | **Stock** short beep (was a long countdown track) |
| `transition_stinger.mp3` | clear/fail | **Stock** tone for now |

Also present as aliases: `score_positive.mp3`, `score_negative.mp3`, `countdown_tick.mp3`.
