# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: game_running.py

import decimal, os, shelve, shutil, sys, time, traceback, zipfile
import loguru
from game_play.Play import Play
from game_play.game_hw import GameHW
from game_play.game_music import GameMusic
from game_play.game_util import GameUtil
from led import led_control
from model.setting import Setting, Color

# Headless mock for LedTable (replaces GUI version)
class LedTable:
    """Mock LED table for headless mode - tracks LED state without UI display"""
    def __init__(self, root=None, wall_light_arr_len=0, led_row=0, led_col=0, table_display=False):
        self.wall_light_arr_len = wall_light_arr_len
        self.led_row = led_row or 16
        self.led_col = led_col or 26
        self.table_display = table_display
        self.hex_buttons = []
        self.led_state = {}

        # Initialize LED table grid (Play class expects this).
        # Each cell holds 3 ring colors [outer, mid, inner] (all black at start).
        self.led_table = [[[(0, 0, 0), (0, 0, 0), (0, 0, 0)] for _ in range(self.led_col)]
                          for _ in range(self.led_row)]
        self.state_table = [[0 for _ in range(self.led_col)] for _ in range(self.led_row)]
        self.wall_light_arr = []
        self.wall_light_state_array = []
        self.wall_screen_arr = []
        self.g_wall_has_been_tread_arr2 = []

    def update_led(self, *args, **kwargs):
        """Mock LED update - just track state, no display"""
        pass

    def redraw_led_table_default(self):
        """Mock LED reset - no display"""
        pass

    def get_state_table(self):
        """Return state table for game logic"""
        return self.state_table

    def get_state_2array(self):
        """Return 2D state array"""
        return self.state_table

    # --- Player press input (replaces hardware floor sensors) ---
    @property
    def table_state(self):
        """Alias used by scoring code: 1 = tile currently pressed."""
        return self.state_table

    def press_cell(self, i, j):
        """Mark a tile as pressed (player stepped on it)."""
        if 0 <= i < self.led_row and 0 <= j < self.led_col:
            self.state_table[i][j] = 1

    def release_cell(self, i, j):
        """Clear a pressed tile."""
        if 0 <= i < self.led_row and 0 <= j < self.led_col:
            self.state_table[i][j] = 0

    def get_wall_light_arr(self):
        """Return wall light array"""
        return self.wall_light_arr

    def get_wall_light_state_array(self):
        """Return wall light state"""
        return self.wall_light_state_array

    def get_wall_screen_arr(self):
        """Return wall screen array"""
        return self.wall_screen_arr

    def get_g_wall_has_been_tread_arr2(self):
        """Return wall tread state"""
        return self.g_wall_has_been_tread_arr2

    def set_table_color(self, table, color):
        """Fill entire grid with single color (data only, no display)"""
        for i in range(self.led_row):
            for j in range(self.led_col):
                table[i][j] = color

    @staticmethod
    def _color_to_rings(color):
        """Each tile has 3 concentric rings: [outer, mid, inner].
        Level color is nested [(r,g,b),(r,g,b),(r,g,b)] = the 3 ring colors.
        A flat (r,g,b) is broadcast to all 3 rings. Returns a 3-ring list."""
        if isinstance(color, (list, tuple)) and len(color) > 0:
            if isinstance(color[0], (list, tuple)):
                rings = [tuple(c) for c in color[:3]]
                while len(rings) < 3:
                    rings.append(rings[-1])
                return rings
            rgb = tuple(color)
            return [rgb, rgb, rgb]  # flat -> same on all rings
        return [(0, 0, 0), (0, 0, 0), (0, 0, 0)]

    def set_color_table_by_set_cell(self, set_cell, color):
        """Write the full 3-ring color into led_table for each cell.
        set_cell = set/list of (i, j) coords. color = nested 3-ring or flat."""
        if not set_cell:
            return
        rings = self._color_to_rings(color)
        for cell in set_cell:
            i = round(cell[0])
            j = round(cell[1])
            if 0 <= i < self.led_row and 0 <= j < self.led_col:
                self.led_table[i][j] = rings

    @staticmethod
    def _cell_channel_max(cell, ch):
        """Max value of channel ch across a cell's rings. Cell may be a
        3-ring list [(r,g,b),...] or a flat (r,g,b)."""
        try:
            if isinstance(cell, (list, tuple)) and len(cell) > 0 \
                    and isinstance(cell[0], (list, tuple)):
                return max(ring[ch] for ring in cell)
            return cell[ch]  # flat
        except Exception:
            return 0

    # Per-channel views derived from led_table (Play reads these).
    # Use max across rings so "is there red/green/blue" works regardless
    # of which ring carries the color.
    @property
    def red_table(self):
        return [[self._cell_channel_max(self.led_table[i][j], 0)
                 for j in range(self.led_col)] for i in range(self.led_row)]

    @property
    def green_table(self):
        return [[self._cell_channel_max(self.led_table[i][j], 1)
                 for j in range(self.led_col)] for i in range(self.led_row)]

    @property
    def blue_table(self):
        return [[self._cell_channel_max(self.led_table[i][j], 2)
                 for j in range(self.led_col)] for i in range(self.led_row)]

    @property
    def goal_color(self):
        return getattr(self, '_goal_color', (0, 254, 0))  # Color.GREEN

    @goal_color.setter
    def goal_color(self, value):
        self._goal_color = value

    @property
    def safe_color(self):
        return (0, 0, 0)  # Color.BLACK

class GameSettingRead:

    def __init__(self):
        try:
            f = shelve.open("./setting/led_parameter")
            try:
                self.wall_light_layout_real = f.get("wall_light_layout_real")
                self.wall_light_layout_logic = f.get("wall_light_layout_logic")
            except:
                self.wall_light_layout_real = None
                self.wall_light_layout_logic = None

            try:
                self.corner_line_start = f.get("corner_line_start")
            except:
                self.corner_line_start = 0

            try:
                self.list_com_info = f.get("list_com_info")
            except:
                self.list_com_info = None

            try:
                self.list_wall_com_info = f.get("list_wall_com_info")
            except:
                self.list_wall_com_info = None

            try:
                self.list_screen_com_info = f.get("list_screen_com_info")
            except:
                self.list_screen_com_info = None

            try:
                self.value_high = f.get("value_high")
            except:
                self.value_high = 0

            try:
                self.value_width = f.get("value_width")
            except:
                self.value_width = 0

            try:
                self.game_idle_video = f.get["game_idle_video_sw"]
            except:
                self.game_idle_video = ""

            try:
                self.type = f.get("led_layout_type")
            except:
                self.type = "left"

            try:
                self.floor_layout_coors_no_use = f.get("floor_layout_coors_no_use")
            except:
                self.floor_layout_coors_no_use = None

            try:
                self.wall_light_table = f.get("wall_light_table")
            except:
                self.wall_light_table = []

            try:
                self.game_idle_video = f.get("game_idle_video_sw")
            except:
                self.game_idle_video = ""

            try:
                self.local_music = f.get("local_music_sw")
            except:
                self.local_music = ""

            try:
                self.game_name = f.get("game_name_sw")
            except:
                self.game_name = ""

            try:
                self.game_bg_audio = f.get("game_bg_audio_sw")
            except:
                self.game_bg_audio = ""

            try:
                self.game_start_video = f.get("game_start_video_sw")
            except:
                self.game_start_video = ""

            try:
                self.game_blood = f.get("game_blood_sw")
            except:
                self.game_blood = ""

            try:
                self.game_scode = f.get("game_scode_sw")
            except:
                self.game_scode = ""

            try:
                self.game_pass = f.get("game_pass_sw")
            except:
                self.game_pass = ""

            try:
                self.light = f.get("wall_light")
            except:
                self.light = False

            try:
                self.screen = f.get("screen_light")
            except:
                self.screen = False

            f.close()
        except:
            loguru.logger.error(" read setting para {}", traceback.format_exc())
            f.close()


class GameRunning:

    def half_up(self, data):
        return int(decimal.Decimal(data).quantize((decimal.Decimal("0")), rounding=(decimal.ROUND_HALF_UP)))

    def move_range_zone_in_out(self, move_range=[
 (
  0, Setting.ROW), (0, Setting.COL)], area_before=[
 (
  0, Setting.ROW), (0, Setting.COL)], area_after=[(0, Setting.ROW), (0, Setting.COL)]):
        row_before, col_before = area_before
        row_after, col_after = area_after
        multiple_row = row_after / row_before
        multiple_col = col_after / col_before
        zone_middle_row = (move_range[0][0] + move_range[0][1]) / 2
        zone_middle_col = (move_range[1][0] + move_range[1][1]) / 2
        zone_edge_row = (move_range[0][1] - move_range[0][0]) / 2
        zone_edge_col = (move_range[1][1] - move_range[1][0]) / 2
        zone_middle_row_new = zone_middle_row * multiple_row
        zone_middle_col_new = zone_middle_col * multiple_col
        zone_edge_row_new = zone_edge_row * multiple_row
        zone_edge_col_new = zone_edge_col * multiple_col
        zone_range_row_from = self.half_up(zone_middle_row_new - zone_edge_row_new)
        zone_range_row_to = self.half_up(zone_middle_row_new + zone_edge_row_new)
        zone_range_col_from = self.half_up(zone_middle_col_new - zone_edge_col_new)
        zone_range_col_to = self.half_up(zone_middle_col_new + zone_edge_col_new)
        move_range_new = [
         (
          zone_range_row_from, zone_range_row_to), (zone_range_col_from, zone_range_col_to)]
        return move_range_new

    def on_the_edge_of_row(self, coors_before=[], cell_set=[]):
        row_edge = coors_before[0] - 1
        for coors in cell_set:
            row = coors[0]
            if row == 0:
                return 0
                if row == row_edge:
                    return row_edge

        return -1

    def on_the_edge_of_col(self, coors_before=[], cell_set=[]):
        col_edge = coors_before[1] - 1
        for coors in cell_set:
            col = coors[1]
            if col == 0:
                return 0
                if col == col_edge:
                    return col_edge

        return -1

    def zone_in_out_old(self, coors_before=[], coors_after=[], cell_set=None, side=Setting.SIDE_NONE):
        border = 0
        cell_width = 30
        cell_high = 30
        if cell_set is not None:
            cell_set_after = set()
            row_before, col_before = coors_before
            row_after, col_after = coors_after
            multiple_row = row_after / row_before
            multiple_col = col_after / col_before
            for cell in cell_set:
                coors_row_middle_before = (2 * cell[0] + 1) / 2
                row_edge_before = 0.5
                coors_row_before_min = coors_row_middle_before
                coors_row_before_max = row_edge_before
                coors_col_middle_before = (2 * cell[1] + 1) / 2
                col_edge_before = 0.5
                coors_col_before_min = coors_col_middle_before
                coors_col_before_max = col_edge_before
                if side == Setting.SIDE_BOTH:
                    coors_row_after_min = coors_row_before_min * multiple_row
                    coors_row_after_max = coors_row_before_max * multiple_row
                    coors_col_after_min = coors_col_before_min * multiple_col
                    coors_col_after_max = coors_col_before_max * multiple_col
                    row_after_min = coors_row_after_min - coors_row_after_max
                    row_after_max = coors_row_after_min + coors_row_after_max
                    col_after_min = coors_col_after_min - coors_col_after_max
                    col_after_max = coors_col_after_min + coors_col_after_max
                    row_edge_after = coors_row_after_max
                    col_edge_after = coors_col_after_max
                else:
                    if side == Setting.SIDE_ROW:
                        coors_row_after_min = coors_row_before_min * multiple_row
                        coors_row_after_max = coors_row_before_max * multiple_row
                        row_after_min = coors_row_after_min - coors_row_after_max
                        row_after_max = coors_row_after_min + coors_row_after_max
                        on_the_edge = self.on_the_edge_of_col(coors_before, cell_set)
                        if on_the_edge == 0:
                            coors_col_after_min = cell[1]
                            coors_col_after_max = cell[1] + 1
                        else:
                            if on_the_edge > 0:
                                coors_col_after_min = col_after - (col_before - cell[1])
                                coors_col_after_max = coors_col_after_min + 1
                            else:
                                coors_col_after_min = cell[1] + (col_after - col_before) / 2
                                coors_col_after_max = cell[1] + 1 + (col_after - col_before) / 2
                        col_after_min = coors_col_after_min
                        col_after_max = coors_col_after_max
                        row_edge_after = coors_row_after_max
                        col_edge_after = 0.5
                    else:
                        if side == Setting.SIDE_COL:
                            coors_col_after_min = coors_col_before_min * multiple_col
                            coors_col_after_max = coors_col_before_max * multiple_col
                            col_after_min = coors_col_after_min - coors_col_after_max
                            col_after_max = coors_col_after_min + coors_col_after_max
                            on_the_edge = self.on_the_edge_of_row(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_row_after_min = cell[0]
                                coors_row_after_max = cell[0] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_row_after_min = row_after - (row_before - cell[0])
                                    coors_row_after_max = coors_row_after_min + 1
                                else:
                                    coors_row_after_min = cell[0] + (row_after - row_before) / 2
                                    coors_row_after_max = cell[0] + 1 + (row_after - row_before) / 2
                            row_after_min = coors_row_after_min
                            row_after_max = coors_row_after_max
                            row_edge_after = 0.5
                            col_edge_after = coors_col_after_max
                        else:
                            on_the_edge = self.on_the_edge_of_col(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_col_after_min = cell[1]
                                coors_col_after_max = cell[1] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_col_after_min = col_after - (col_before - cell[1])
                                    coors_col_after_max = coors_col_after_min + 1
                                else:
                                    coors_col_after_min = cell[1] + (col_after - col_before) / 2
                                    coors_col_after_max = cell[1] + 1 + (col_after - col_before) / 2
                            on_the_edge = self.on_the_edge_of_row(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_row_after_min = cell[0]
                                coors_row_after_max = cell[0] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_row_after_min = row_after - (row_before - cell[0])
                                    coors_row_after_max = coors_row_after_min + 1
                                else:
                                    coors_row_after_min = cell[0] + (row_after - row_before) / 2
                                    coors_row_after_max = cell[0] + 1 + (row_after - row_before) / 2
                            row_after_min = coors_row_after_min
                            row_after_max = coors_row_after_max
                            col_after_min = coors_col_after_min
                            col_after_max = coors_col_after_max
                            row_edge_after = 0.5
                            col_edge_after = 0.5
                row_after_min = self.half_up(row_after_min)
                row_after_max = self.half_up(row_after_max)
                col_after_min = self.half_up(col_after_min)
                col_after_max = self.half_up(col_after_max)
                int_row_after_min = self.half_up(row_after_min)
                if row_after_min < 0:
                    row_after_min = 0
                if row_after_max > row_after:
                    row_after_max = row_after
                if col_after_min < 0:
                    col_after_min = 0
                if col_after_max > col_after:
                    col_after_max = col_after
                if row_after_min == row_after_max:
                    row_after_max = row_after_min + 1
                if col_after_min == col_after_max:
                    col_after_max = col_after_min + 1
                for i in range(row_after_min, row_after_max):
                    for j in range(col_after_min, col_after_max):
                        cell_set_after.add((i, j))

            return cell_set_after
        return

    def zone_in_out(self, coors_before=[], coors_after=[], cell_set=None, side=Setting.SIDE_NONE):
        if cell_set is not None:
            cell_set_after = set()
            row_before, col_before = coors_before
            row_after, col_after = coors_after
            multiple_row = row_after / row_before
            multiple_col = col_after / col_before
            min_row, max_row = (10000, 1)
            min_col, max_col = (10000, 1)
            for cell in cell_set:
                if cell[0] < min_row:
                    min_row = cell[0]
                if cell[0] > max_row:
                    max_row = cell[0]
                if cell[1] < min_col:
                    min_col = cell[1]
                if cell[1] > max_col:
                    max_col = cell[1]

            cen_row = (min_row + max_row) / 2.0
            cen_col = (min_col + max_col) / 2.0
            center_col_after = cen_col * multiple_col
            center_row_after = cen_row * multiple_row
            for cell in cell_set:
                coors_row_middle_before = (2 * cell[0] + 1) / 2
                row_edge_before = 0.5
                coors_row_before_min = coors_row_middle_before
                coors_row_before_max = row_edge_before
                coors_col_middle_before = (2 * cell[1] + 1) / 2
                col_edge_before = 0.5
                coors_col_before_min = coors_col_middle_before
                coors_col_before_max = col_edge_before
                if side == Setting.SIDE_BOTH:
                    coors_row_after_min = coors_row_before_min * multiple_row
                    coors_row_after_max = coors_row_before_max * multiple_row
                    coors_col_after_min = coors_col_before_min * multiple_col
                    coors_col_after_max = coors_col_before_max * multiple_col
                    row_after_min = coors_row_after_min - coors_row_after_max
                    row_after_max = coors_row_after_min + coors_row_after_max
                    col_after_min = coors_col_after_min - coors_col_after_max
                    col_after_max = coors_col_after_min + coors_col_after_max
                else:
                    if side == Setting.SIDE_ROW:
                        coors_row_after_min = coors_row_before_min * multiple_row
                        coors_row_after_max = coors_row_before_max * multiple_row
                        row_after_min = coors_row_after_min - coors_row_after_max
                        row_after_max = coors_row_after_min + coors_row_after_max
                        on_the_edge = self.on_the_edge_of_col(coors_before, cell_set)
                        if on_the_edge == 0:
                            coors_col_after_min = cell[1]
                            coors_col_after_max = cell[1] + 1
                        else:
                            if on_the_edge > 0:
                                coors_col_after_min = col_after - (col_before - cell[1])
                                coors_col_after_max = coors_col_after_min + 1
                            else:
                                coors_col_after_min = cell[1] - cen_col + center_col_after
                                coors_col_after_max = cell[1] - cen_col + center_col_after + 1
                        col_after_min = coors_col_after_min
                        col_after_max = coors_col_after_max
                    else:
                        if side == Setting.SIDE_COL:
                            coors_col_after_min = coors_col_before_min * multiple_col
                            coors_col_after_max = coors_col_before_max * multiple_col
                            col_after_min = coors_col_after_min - coors_col_after_max
                            col_after_max = coors_col_after_min + coors_col_after_max
                            on_the_edge = self.on_the_edge_of_row(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_row_after_min = cell[0]
                                coors_row_after_max = cell[0] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_row_after_min = row_after - (row_before - cell[0])
                                    coors_row_after_max = coors_row_after_min + 1
                                else:
                                    coors_row_after_min = cell[0] - cen_row + center_row_after
                                    coors_row_after_max = cell[0] - cen_row + center_row_after + 1
                            row_after_min = coors_row_after_min
                            row_after_max = coors_row_after_max
                        else:
                            on_the_edge = self.on_the_edge_of_col(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_col_after_min = cell[1]
                                coors_col_after_max = cell[1] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_col_after_min = col_after - (col_before - cell[1])
                                    coors_col_after_max = coors_col_after_min + 1
                                else:
                                    coors_col_after_min = cell[1] - cen_col + center_col_after
                                    coors_col_after_max = cell[1] - cen_col + center_col_after + 1
                            on_the_edge = self.on_the_edge_of_row(coors_before, cell_set)
                            if on_the_edge == 0:
                                coors_row_after_min = cell[0]
                                coors_row_after_max = cell[0] + 1
                            else:
                                if on_the_edge > 0:
                                    coors_row_after_min = row_after - (row_before - cell[0])
                                    coors_row_after_max = coors_row_after_min + 1
                                else:
                                    coors_row_after_min = cell[0] - cen_row + center_row_after
                                    coors_row_after_max = cell[0] - cen_row + center_row_after + 1
                            row_after_min = coors_row_after_min
                            row_after_max = coors_row_after_max
                            col_after_min = coors_col_after_min
                            col_after_max = coors_col_after_max
                row_after_min = self.half_up(round(row_after_min, 2))
                row_after_max = self.half_up(round(row_after_max, 2))
                col_after_min = self.half_up(round(col_after_min, 2))
                col_after_max = self.half_up(round(col_after_max, 2))
                int_row_after_min = self.half_up(row_after_min)
                if row_after_min < 0:
                    row_after_min = 0
                if row_after_max > row_after:
                    row_after_max = row_after
                if col_after_min < 0:
                    col_after_min = 0
                if col_after_max > col_after:
                    col_after_max = col_after
                if row_after_min == row_after_max:
                    row_after_max = row_after_min + 1
                if col_after_min == col_after_max:
                    col_after_max = col_after_min + 1
                for i in range(row_after_min, row_after_max):
                    for j in range(col_after_min, col_after_max):
                        cell_set_after.add((i, j))

            return cell_set_after
        return

    def group_area_transform(self, game, tmp_dict_group, setting):
        last_game_exist_wall = False
        cur_game_exist_wall = False
        last_game_area_adaption = game.game_area_adaption
        layout_row = int(setting.value_high)
        layout_col = int(setting.value_width)
        corner_line_start = setting.corner_line_start
        if game.corner_line_start > 0:
            last_game_exist_wall = True
        if corner_line_start > 0:
            cur_game_exist_wall = True
        if cur_game_exist_wall and last_game_exist_wall:
            for key, group in tmp_dict_group.items():
                if group.start_area == 1:
                    new_group_member = []
                    for coors in group.start_member:
                        new_group_member.append((coors[0], coors[1] - game.corner_line_start))

                    group.start_member = new_group_member
                group_col_from = group.activity_area[1][0]
                group_col_to = group.activity_area[1][1]
                if group_col_from >= game.corner_line_start:
                    size_floor_before = [
                     game.row, game.col - game.corner_line_start]
                    size_floor_after = [layout_row, layout_col - corner_line_start]
                    group.activity_area[1] = (group.activity_area[1][0] - game.corner_line_start,
                     group.activity_area[1][1] - game.corner_line_start)
                    group.activity_area = self.move_range_zone_in_out(group.activity_area, size_floor_before, size_floor_after)
                    group.activity_area[1] = (corner_line_start + group.activity_area[1][0],
                     corner_line_start + group.activity_area[1][1])
                elif group_col_to <= game.corner_line_start:
                    size_wall_before = [
                     game.row, game.corner_line_start]
                    size_wall_after = [layout_row, corner_line_start]
                    group.activity_area = self.move_range_zone_in_out(group.activity_area, size_wall_before, size_wall_after)
                else:
                    size_wall_before = [
                     game.row, game.corner_line_start]
                    size_wall_after = [layout_row, corner_line_start]
                    activity_area_wall = [group.activity_area[0],
                     (
                      group.activity_area[1][0], game.corner_line_start)]
                    activity_area_wall = self.move_range_zone_in_out(activity_area_wall, size_wall_before, size_wall_after)
                    size_floor_before = [game.row, game.col - game.corner_line_start]
                    size_floor_after = [layout_row,
                     layout_col - corner_line_start]
                    activity_area_floor = [group.activity_area[0],
                     (
                      group.activity_area[1][0] - game.corner_line_start,
                      group.activity_area[1][1] - game.corner_line_start)]
                    activity_area_floor = self.move_range_zone_in_out(activity_area_floor, size_floor_before, size_floor_after)
                    group.activity_area = [activity_area_wall[0],
                     (
                      activity_area_wall[1][0],
                      activity_area_floor[1][1] + corner_line_start)]

        else:
            if not cur_game_exist_wall:
                if last_game_exist_wall:
                    if last_game_area_adaption:
                        for key, group in tmp_dict_group.items():
                            if group.start_area == 0:
                                group.start_area = 1
                            size_before = [
                             game.row, game.col]
                            size_after = [layout_row, layout_col]
                            group.activity_area = self.move_range_zone_in_out(group.activity_area, size_before, size_after)

                else:
                    loguru.logger.error("Game self-adaptation failed")
                    return False
            else:
                if cur_game_exist_wall and not last_game_exist_wall:
                    for key, group in tmp_dict_group.items():
                        size_before = [
                         game.row, game.col]
                        size_after = [layout_row, layout_col - corner_line_start]
                        group.activity_area = self.move_range_zone_in_out(group.activity_area, size_before, size_after)
                        group.activity_area[1] = (corner_line_start + group.activity_area[1][0],
                         corner_line_start + group.activity_area[1][1])

                else:
                    for key, group in tmp_dict_group.items():
                        size_before = [
                         game.row, game.col]
                        size_after = [layout_row, layout_col]
                        group.activity_area = self.move_range_zone_in_out(group.activity_area, size_before, size_after)

        return True

    def group_size_scale(self, game, dict_group, setting):
        row = int(setting.value_high)
        col = int(setting.value_width)
        platform_size = [row, col]
        layout_corner_line_start = setting.corner_line_start
        if not self.group_area_transform(game, dict_group, setting):
            return
        for key in dict_group.keys():
            group = dict_group[key]
            if group.type == Setting.FLOOR_LIGHT:
                if layout_corner_line_start == 0:
                    group_member = self.zone_in_out([
                     game.row, game.col], platform_size, group.start_member, group.scale)
                    group.start_member = group_member
                else:
                    if group.start_area == 0:
                        group_member = self.zone_in_out([
                         game.row, game.corner_line_start], [platform_size[0], layout_corner_line_start], group.start_member, group.scale)
                        group.start_member = group_member
                    else:
                        group_member = self.zone_in_out([
                         game.row, game.col - game.corner_line_start], [
                         platform_size[0], platform_size[1] - layout_corner_line_start], group.start_member, group.scale)
                        new_grop_member = []
                        for coors in group_member:
                            new_grop_member.append((coors[0], coors[1] + layout_corner_line_start))

                        group.start_member = new_grop_member
                continue

        row_resize = row / game.row
        col_resize = col / game.col
        tmp = round(game.zone_row_from * row_resize)
        game.zone_row_from = tmp
        tmp = round(game.zone_col_from * col_resize)
        game.zone_col_from = tmp
        game.zone_row_to = round(game.zone_row_to * row_resize)
        game.zone_col_to = round(game.zone_col_to * col_resize)

    def unzipfile(self, game_zip_path):
        try:
            with zipfile.ZipFile(game_zip_path + ".led", "r") as myzip:
                for file in myzip.namelist():
                    myzip.extract(file, path=game_zip_path)

            myzip.close()
        except:
            loguru.logger.error(traceback.format_exc())

    def remove_file_after_zip(self, game_zip_path):
        try:
            shutil.rmtree(game_zip_path)
        except:
            loguru.logger.error(traceback.format_exc())

    def clear_last_wall_display(self, color=[Color.BLACK] * 3):
        for i in range(len(self.led_table.led_table)):
            for j in range(len(self.led_table.led_table[0])):
                self.led_table.led_table[i][j] = color

    def get_max_end_time_in_group_by_dict_group(self, dict_group):
        max_end_time = 0
        for key, value in dict_group.items():
            end_time = value.end_time_sec
            if end_time > max_end_time:
                max_end_time = end_time

        return max_end_time

    def is_game_over(self, total_time):
        if self.game_life_time < total_time:
            self.play.stop_running()
        else:
            return

    def update_video_play(self):
        if self.video_play is not None and self.video_play.video is not None:
            self.video_play.update_frame()
        else:
            if self.game_path is None or self.game_path == "":
                self.close_game()

    def update_draw_led_table_idle_game(self, dict_group, total_pass=0, time_pass=0):
        self.clear_last_wall_display()
        for key, value in dict_group.items():
            group = value
            set_cell = group.start_member
            start_time = group.start_time_sec
            end_time = group.end_time_sec
            if set_cell is not None and total_pass > start_time and total_pass < end_time:
                if group.type == Setting.FLOOR_LIGHT:
                    self.led_table.set_color_table_by_set_cell(set_cell, group.color)
                else:
                    if group.type == Setting.SCREEN_LIGHT:
                        self.led_table.draw_led_table_text_by_group(group)
                        i = 0
                        for index in group.start_member:
                            self.led_table.get_wall_screen_arr()[index] = group.text[i]
                            i += 1

                    else:
                        i = 0
                        try:
                            for index in group.start_member:
                                str_t = group.color
                                tuple_tmp = (
                                 int((str_t[1[:3]]), base=16), int((str_t[3[:5]]), base=16), int((str_t[5[:7]]), base=16))
                                self.led_table.get_wall_light_arr()[index] = tuple_tmp
                                i += 1

                        except:
                            pass

                        continue

        self.led_table.redraw_led_table_default(draw_canvas=False)
        if Setting.USE_SERIAL_HD:
            self.game_hw.draw_hw_led_color()
        if self.root:
            self.root.update()
        self.is_game_over(total_pass)

    def read_game_info_and_running(self, game_path, setting):
        self.unzipfile(game_path)
        for game_folder in os.listdir(game_path):
            if self.circle_game:
                game_name = os.path.join(game_path + "/" + game_folder, "game_file")
                db = shelve.open(game_name)
                dict_group = db[Setting.PARA_KEY_GAME_GROUP]
                game = db[Setting.PARA_KEY_GAME]
                db.close()
                self.group_size_scale(game, dict_group, setting)
                game_music = GameMusic((self.root), setting, (game_path + "/" + game_folder), game, music_from=False)
                self.game_music = game_music
                game_music.music("introduce", True)
                self.game_life_time = self.get_max_end_time_in_group_by_dict_group(dict_group)
                if self.circle_game:
                    self.play.running_new(dict_group, game, idle=True, delay_time=(self.delay_time), parent=self)
                game_music.music("game_success", True)
                game_music.music("stop")
            else:
                break

        self.remove_file_after_zip(game_path)

    def __init__(self, parent=None, game_path=None, setting=None):
        self.setting = GameSettingRead()
        game_path = self.setting.game_idle_video
        game_path = game_path.split(".")[0]
        self.game_path = game_path
        self.root = None
        self.circle_game = True
        self.game_life_time = 0
        led_row = int(self.setting.value_high)
        led_col = int(self.setting.value_width)
        wall_light_arr_len = len(self.setting.wall_light_table)
        self.game_hw = None
        self.play = None
        self.led_table = LedTable((self.root), wall_light_arr_len, led_row, led_col, table_display=False)
        self.game_level = 1
        self.play = Play(self.led_table)
        self.game_music = None
        self.delay_time = 5
        self.video_play = None
        self.video_play = None

    def star_running(self):
        try:
            if not led_control.g_has_open:
                if Setting.USE_SERIAL_HD:
                    loguru.logger.info("start of game idle")
                    self.circle_game = True
                    if self.game_path is not None and self.game_path != "":
                        self.game_hw = GameHW(self.setting, self.led_table)
                        while self.circle_game:
                            try:
                                self.read_game_info_and_running(self.game_path, self.setting)
                            except:
                                loguru.logger.error("idle game: {}", traceback.format_exc())

                        loguru.logger.info("end of game idle")
            else:
                loguru.logger.info("led_control not opens or not setting USE_SERIAL_HD")
        except:
            loguru.logger.error(traceback.format_exc())

    def star_running_new(self, setting, partial_update_ui):
        loguru.logger.info("Idle Game Play In Process")
        self.circle_game = True
        if self.game_path is not None:
            if self.game_path != "":
                self.game_hw = GameHW(self.setting, self.led_table)
                game_unzip_dir = self.game_path
                try:
                    self.game_util.unzipfile(game_unzip_dir)
                    loguru.logger.info("game_unzip_dir")
                    game_unzip_dir = os.path.splitext(game_unzip_dir)[0]
                    while self.circle_game:
                        try:
                            for game_folder in os.listdir(game_unzip_dir):
                                loguru.logger.info(game_folder)
                                if self.circle_game:
                                    game, dict_group = self.game_util.read_game_and_group(game_unzip_dir, game_folder, setting)
                                    self.cur_game_time = self.game_util.get_max_end_time_in_all_group(dict_group)
                                    game_folder_path = game_unzip_dir + "/" + game_folder
                                    self.game_life_time = self.get_max_end_time_in_group_by_dict_group(dict_group)
                                    if self.circle_game:
                                        self.play.running_new(dict_group, game, idle=True, delay_time=(self.delay_time), parent=self)

                        except:
                            loguru.logger.error(traceback.format_exc())

                    self.game_util.remove_unzipfile(game_unzip_dir)
                except:
                    loguru.logger.error(traceback.format_exc())

                loguru.logger.debug("end of game idle running")
        self.cur_game_name = game_unzip_dir

    def close_game(self):
        loguru.logger.info("call close_game idle")
        if self.game_hw is not None:
            self.clear_last_wall_display()
            self.led_table.redraw_led_table_default()
            self.game_hw.draw_hw_led_color()
            self.game_hw.hw_led_close()
        if self.play is not None:
            self.play.stop_running()
        self.circle_game = False
        if self.game_music is not None:
            self.game_music.music_close()
        if self.video_play is not None:
            self.video_play.stop_video()

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/game_play/game_running.pyc
