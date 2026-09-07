"""Production transition .led assets must stay below serial sync byte 255."""
from __future__ import annotations

import glob
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.game_manager import _load_level_file, _normalize_rings

PROD_EFFECTS_DIR = ROOT / "games" / "source" / "effects"
EFFECT_NAMES = ("countdown", "level_clear", "level_fail")
GAMES_ROOT = ROOT / "games"
LEVEL_GLOBS = (
    "source/-/*.led",
    "source/--/*.led",
    "source/---/*.ledb",
    "source_group/-/*.led",
    "source_group/--/*.led",
)


def _collect_group_rgbs(dict_group) -> set[tuple[int, int, int]]:
    colors: set[tuple[int, int, int]] = set()
    for group in dict_group.values():
        for rings in _normalize_rings(getattr(group, "color", None)):
            colors.add(tuple(int(channel) for channel in rings[:3]))
    return colors


def _iter_production_levels():
    for pattern in LEVEL_GLOBS:
        for path in sorted(glob.glob(str(GAMES_ROOT / pattern))):
            yield path


class ProductionEffectsRgbTests(unittest.TestCase):
    def test_production_transition_assets_avoid_sync_byte(self):
        for name in EFFECT_NAMES:
            path = PROD_EFFECTS_DIR / f"{name}.led"
            self.assertTrue(path.is_file(), f"missing production effect: {path}")
            dict_group, game_obj = _load_level_file(str(path))
            self.assertIsNotNone(dict_group, f"could not decode {path}")
            self.assertIsNotNone(game_obj, f"missing game metadata in {path}")

            colors = _collect_group_rgbs(dict_group)
            self.assertTrue(colors, f"{name} has no authored colors")
            self.assertFalse(
                any(channel == 255 for rgb in colors for channel in rgb),
                f"{name} contains RGB channel 255: {sorted(colors)}",
            )

    def test_production_transition_assets_are_not_all_black(self):
        for name in EFFECT_NAMES:
            path = PROD_EFFECTS_DIR / f"{name}.led"
            dict_group, _ = _load_level_file(str(path))
            colors = _collect_group_rgbs(dict_group)
            self.assertTrue(
                any(any(channel > 0 for channel in rgb) for rgb in colors),
                f"{name} is all black",
            )

    def test_all_production_levels_avoid_sync_byte(self):
        paths = list(_iter_production_levels())
        self.assertGreaterEqual(len(paths), 60, "expected production level archives")
        offenders = []
        for path in paths:
            dict_group, _ = _load_level_file(path)
            self.assertIsNotNone(dict_group, f"could not decode {path}")
            colors = _collect_group_rgbs(dict_group)
            bad = [rgb for rgb in colors if any(channel == 255 for channel in rgb)]
            if bad:
                offenders.append((os.path.basename(path), bad))
        self.assertFalse(offenders, f"levels with RGB 255: {offenders}")


if __name__ == "__main__":
    unittest.main()
