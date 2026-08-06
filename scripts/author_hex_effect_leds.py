#!/usr/bin/env python3
"""Generate Hexagon effect .led archives (5×9 / 33 live tiles).

Usage:
  python scripts/author_hex_effect_leds.py [--out DIR] [--fast]

Default output: games/source/effects/
--fast: shorter holds for tests/fixtures (writes to tests/fixtures/effects when --out omitted)
"""

from __future__ import annotations

import argparse
import os
import shelve
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GAMES_ROOT = REPO_ROOT / "games"
sys.path.insert(0, str(GAMES_ROOT))

from model.game import Game
from model.group import Group
from model.setting import Color, Setting


def _live_coords() -> list[tuple[int, int]]:
    import shelve as _shelve

    db = _shelve.open(str(GAMES_ROOT / "setting" / "led_parameter"), flag="r")
    dead = {tuple(c) for c in db.get("floor_layout_coors_no_use", [])}
    rows = int(float(db.get("value_high", 5)))
    cols = int(float(db.get("value_width", 9)))
    db.close()
    live = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in dead]
    if len(live) != 33:
        raise RuntimeError(f"Expected 33 live coords, got {len(live)}")
    return live


def _solid_color(rgb: tuple[int, int, int]) -> list[list[int]]:
    ring = list(rgb)
    return [ring[:], ring[:], ring[:]]


def _make_game() -> Game:
    game = Game(
        name="hex_effect",
        row=5,
        col=9,
        zone_row_from=0,
        zone_row_to=5,
        zone_col_from=0,
        zone_col_to=9,
    )
    game.play_order = False
    game.background = Color.BLACK
    return game


def _group(name: str, members, color, start: float, end: float) -> Group:
    return Group(
        name=name,
        member=set(members),
        start_time_sec=start,
        end_time_sec=end,
        color=_solid_color(color),
        speed=0,
        direct=Setting.STOP,
        gtype=Setting.FLOOR_LIGHT,
        activity_area=[(0, 5), (0, 9)],
    )


def _build_countdown(live, step: float) -> dict:
    total = step * 3
    return {
        "Group(1)": _group("Group(1)", live, (254, 0, 0), 0.0, step),
        "Group(2)": _group("Group(2)", live, (0, 0, 254), step, step * 2),
        "Group(3)": _group("Group(3)", live, (0, 254, 0), step * 2, total),
    }


def _build_hold(live, color, duration: float) -> dict:
    return {"Group(1)": _group("Group(1)", live, color, 0.0, duration)}


def _write_led(path: Path, groups: dict, game: Game) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        shelf_dir = Path(tmp) / "00000"
        shelf_dir.mkdir()
        shelf_path = str(shelf_dir / "game_file")
        db = shelve.open(shelf_path)
        db["dict_group"] = groups
        db["para_key_game"] = game
        db.close()
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in shelf_dir.iterdir():
                if file_path.name.startswith("game_file"):
                    archive.write(file_path, f"00000/{file_path.name}")


def _indicator_group(name, cell, color) -> Group:
    return Group(
        name=name,
        member={cell},
        start_time_sec=0.0,
        end_time_sec=600.0,
        color=_solid_color(color),
        speed=0,
        direct=Setting.STOP,
        gtype=Setting.WALL_LIGHT,
        activity_area=[(0, 5), (0, 9)],
    )


def author_test_levels(out_dir: Path) -> None:
    """Minimal marathon levels for pytest (fast clear + scorable tile)."""
    live = _live_coords()
    game = _make_game()
    out_dir.mkdir(parents=True, exist_ok=True)

    fast = {"Group(1)": _group("Group(1)", live[:5], (100, 100, 100), 0.0, 0.35)}
    _write_led(out_dir / "fast_clear.led", fast, game)

    goal = (2, 4)
    green = (0, 254, 0)
    score = {
        "Group(1)": _indicator_group("Group(1)", goal, green),
        "Group(2)": _group("Group(2)", [goal], green, 0.0, 600.0),
    }
    _write_led(out_dir / "score_once.led", score, game)
    print(f"Wrote test levels to {out_dir}")


def author_effects(out_dir: Path, *, fast: bool = False) -> None:
    live = _live_coords()
    game = _make_game()
    step = 0.05 if fast else 0.8
    hold = 0.1 if fast else 2.5

    specs = {
        "countdown.led": _build_countdown(live, step),
        "level_clear.led": _build_hold(live, (0, 254, 0), hold),
        "level_fail.led": _build_hold(live, (254, 0, 0), hold),
    }
    for filename, groups in specs.items():
        dest = out_dir / filename
        _write_led(dest, groups, game)
        print(f"Wrote {dest} ({len(groups)} groups, {len(live)} tiles/group)")


def main():
    parser = argparse.ArgumentParser(description="Author Hexagon effect .led files")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: games/source/effects or fixtures when --fast)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Short timings for pytest fixtures",
    )
    parser.add_argument(
        "--test-levels",
        action="store_true",
        help="Also write tests/fixtures/levels/*.led",
    )
    args = parser.parse_args()
    if args.out is not None:
        out_dir = args.out
    elif args.fast:
        out_dir = REPO_ROOT / "tests" / "fixtures" / "effects"
    else:
        out_dir = GAMES_ROOT / "source" / "effects"
    author_effects(out_dir, fast=args.fast)
    if args.test_levels or args.fast:
        author_test_levels(REPO_ROOT / "tests" / "fixtures" / "levels")


if __name__ == "__main__":
    main()
