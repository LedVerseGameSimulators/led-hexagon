"""3-ring floor serial encoder must reserve sync byte 255 in payload channels."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


GAMES_DIR = Path(__file__).resolve().parents[1] / "games"
sys.path.insert(0, str(GAMES_DIR))

for _name in list(sys.modules):
    if _name == "led" or _name.startswith("led."):
        del sys.modules[_name]

from led.led_control import (  # noqa: E402
    _encode_wire_color,
    build_floor_wire_frame,
)


def _cell(outer, mid, inner):
    """Hardware stores rings as [inner, mid, outer] at indices 0, 1, 2."""
    return [list(inner), list(mid), list(outer)]


class FloorWireEncoderTests(unittest.TestCase):
    def test_header_preserved(self):
        grid = [[_cell((1, 2, 3), (4, 5, 6), (7, 8, 9))]]
        frame = build_floor_wire_frame(grid, [(0, 0)])
        self.assertEqual(frame[:2], [255, 255])

    def test_ring_order_outer_mid_inner(self):
        grid = [[_cell((10, 11, 12), (20, 21, 22), (30, 31, 32))]]
        frame = build_floor_wire_frame(grid, [(0, 0)])
        self.assertEqual(frame[2:], [10, 11, 12, 20, 21, 22, 30, 31, 32])

    def test_tile_order_is_reversed(self):
        grid = [
            [_cell((1, 0, 0), (1, 0, 0), (1, 0, 0)), _cell((2, 0, 0), (2, 0, 0), (2, 0, 0))],
        ]
        frame = build_floor_wire_frame(grid, [(0, 0), (0, 1)])
        self.assertEqual(len(frame), 2 + 9 * 2)
        self.assertEqual(frame[2:11], [2, 0, 0] * 3)
        self.assertEqual(frame[11:20], [1, 0, 0] * 3)

    def test_frame_length(self):
        grid = [
            [
                _cell((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                _cell((0, 0, 0), (0, 0, 0), (0, 0, 0)),
            ],
            [
                _cell((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                _cell((0, 0, 0), (0, 0, 0), (0, 0, 0)),
            ],
        ]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        frame = build_floor_wire_frame(grid, positions)
        self.assertEqual(len(frame), 2 + 9 * len(positions))

    def test_clamps_255_to_254(self):
        self.assertEqual(_encode_wire_color((255, 255, 255)), (254, 254, 254))

    def test_clamps_above_255(self):
        self.assertEqual(_encode_wire_color((300, 400, 500)), (254, 254, 254))

    def test_clamps_below_zero(self):
        self.assertEqual(_encode_wire_color((-5, -1, 0)), (0, 0, 0))

    def test_payload_never_contains_sync_byte(self):
        grid = [[_cell((255, 255, 255), (300, 0, -1), (0, 255, 0))]]
        frame = build_floor_wire_frame(grid, [(0, 0)])
        self.assertNotIn(255, frame[2:])
        self.assertEqual(frame[2:], [254, 254, 254, 254, 0, 0, 0, 254, 0])


if __name__ == "__main__":
    unittest.main()
