# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui_editor_game2.py
import datetime, os.path, shelve, sys, time, traceback
from loguru import logger
from audio_play import audio
from game_play.game_util import GameUtil
from gui.gui_game_fragment_result import GameFragmentRst
from gui.gui_ui import GuiUI
import gui.language as language
from led import led_control
from model.setting import Setting, Color
from model_in.led_group import LedGroup

class EditorGame2:
    MAX_TIME = 3600

    def __init__(self, parent, parent_last, life_value, list_game, game_time, player_min_num, last_root=None, game_unzip_dir=''):
        logger.info("gui editor game1")
        self.game_util = GameUtil()
        self.game_time = game_time
        self.game_start_time = time.time()
        self.game_record_rt = parent.game_record_rt
        self.game_record_rt.running_to_obj = self
        self.game_record_rt.game_result = 2
        self.game_record_rt.game_blood = life_value
        self.game_record_rt.game_blood_left = 0
        self.game_record_rt.game_blood_right = 0
        self.game_record_rt.game_scode = 0
        self.game_record_rt.game_scode_left = 0
        self.game_record_rt.game_scode_right = 0
        self.main_obj = parent
        self.last_time = 0
        self.total_pass = 0
        self.list_start_time_goal_group = []
        self.list_start_time_goal_group2 = []
        self._two_color_mode = False
        self.life_value = life_value
        self.game_level = parent.game_level
        self.setting = parent.setting
        self.led_col = None
        self.parent = parent
        self.parent_game_running = parent_last
        self.db = parent.db
        self.cur_game_name = None
        self.cur_game_fragment = None
        self.led_col_wall_light = None
        self.led_col_wall_screen = None
        self.led_row = int(self.setting.value_high.get())
        self.led_col = int(self.setting.value_width.get())
        self.blue_hide_max_time = self.setting.blue_hide_max_time.get()
        self.life_cal = None
        self.list_game = list_game
        self.list_game_name = []
        for game_path in self.list_game:
            self.list_game_name.append(os.path.basename(game_path))

        self.circle_game = True
        self.player_nums = 2
        if self.player_nums > 6:
            self.player_nums = 6
        else:
            setting = self.setting
            self.list_group_blink = []
            self.list_group_breath = []
            self.list_hidden_out = []
            self.position_info = [[None] * self.led_col for _ in range(self.led_row)]
            self.init_position_info()
            self.list_hidden_group = []
            self.list_hidden_tread_group = []
            self.list_hidden_coors = []
            self.list_hidden_colors = []
            self.table_cover_show = [[False] * self.led_col for _ in range(self.led_row)]
            self.trigger_span = 1
            self.prompt_cost = self.setting.hidden_prompt_score.get()
            self.prompt_time = self.setting.hidden_show_time.get()
            self.hidn_tread_show_time = self.setting.hidn_tread_show_time.get()
            self.cover_action = "disappear"
            self.blue_hide_max_time = self.setting.blue_hide_max_time.get()
            try:
                f = shelve.open("./setting/debug_parameter")
                self.trigger_span = float(f.get("life_value_count_time"))
                f.close()
            except:
                self.trigger_span = 1.0

            cur_game_fragment = self.parent_game_running.cur_game_fragment
            self.audio_shoot_on = cur_game_fragment.blue_tread
            self.audio_shoot_off = cur_game_fragment.red_tread
            print("player_nums", self.player_nums)
            self.color_scode = [
             0] * self.player_nums
            self.color_bullet = [0] * self.player_nums
            self.arr_count_between_time = [
             10] * (2 * (self.led_row + self.led_col))
            if self.game_record_rt.game_info is None:
                self.total_scode = [
                 0] * self.player_nums
                self.total_bullet = [0] * self.player_nums
                self.game_record_rt.game_info = (self.total_scode, self.total_bullet)
            else:
                self.total_scode = self.game_record_rt.game_info[0]
            self.total_bullet = self.game_record_rt.game_info[1]
        color_array = [(254, 128, 0), (0, 0, 254), (254, 254, 0), (0, 254, 254), 
         (254, 0, 254), 
         (254, 254, 254)]
        self.color_array = [[Color.GRAY, Color.GRAY, Color.GRAY]] * 2
        self.color_error = [Color.RED]
        list_player = []
        for i in range(self.player_nums):
            list_player.append(language.PLAYER + str(i + 1))

        self.list_player_name = list_player
        leval_span = self.setting.leval_span.get()
        self.game_level_speed = self.game_util.get_game_speed(self.game_level, leval_span)
        wall_light_arr_len = len(self.setting.wall_light_table)
        row = int(self.setting.value_high.get())
        col = int(self.setting.value_width.get())
        wall_line = self.setting.corner_line_start.get()
        self.ui = GuiUI(self, life_value, row, col, wall_light_arr_len, wall_line, mode=2)
        pst_goal = (
         self.setting.goal_led_coors_row.get() - 1, self.setting.goal_led_coors_col.get() - 1)
        group_tmp = LedGroup([pst_goal], color=([
         self.ui.color_hex_str2int_arr(self.setting.hidden_prompt_breath_color.get())] * 3))
        self.list_group_breath.append(group_tmp)
        self.play_running(game_unzip_dir, self.setting)

    def init_position_info(self):
        for i in range(self.led_row):
            for j in range(self.led_col):
                self.position_info[i][j] = [[], 0]

    def screen_mouse_click_state_get(self):
        coors_click = self.ui.led_table.led_coors_click
        self.ui.led_table.get_state_table()[coors_click[0][0]][coors_click[0][1]] = coors_click[1]
        coors_click = self.ui.led_table.led_coors_click_wall
        self.ui.led_table.get_wall_light_state_array()[coors_click[0][1]] = coors_click[1]

    def update_draw_led_table_end_of_play(self):
        try:
            self.ui.led_table.clear_led_table()
            led_control.draw_led_color(None, self.ui.led_table.led_table)
        except:
            logger.error("update_draw_led_table_end_of_play{}", traceback.format_exc())

    def customized_function(self):
        audio.Audio().stop()
        self.parent_game_running.customized_function()
        self.circle_game = False
        self.running_state = False
        logger.info("editor ui close")

    def update_hw_led_new(self):
        try:
            if Setting.USE_SERIAL_HD:
                self.parent_game_running.draw_hw_led_color_inc_wal(self.ui.led_table)
                self.ui.update_ui(self.game_record_rt)
                self.parent_game_running.get_hw_led_state_inc_wal(self.ui.led_table)
            else:
                self.ui.led_table.draw_led_color()
                self.ui.update_ui(self.game_record_rt)
                self.screen_mouse_click_state_get()
        except:
            logger.error(traceback.format_exc())

    def get_hw_led_state(self):
        try:
            if Setting.USE_SERIAL_HD:
                self.parent_game_running.get_hw_led_state_inc_wal(self.ui.led_table)
            else:
                self.screen_mouse_click_state_get()
        except:
            logger.error(traceback.format_exc())

    def draw_hw_led_color(self):
        try:
            if Setting.USE_SERIAL_HD:
                self.parent_game_running.draw_hw_led_color_inc_wal(self.ui.led_table)
                self.ui.update_ui(self.game_record_rt)
            else:
                self.ui.update_ui(self.game_record_rt)
        except:
            logger.error(traceback.format_exc())

    def get_group_state(self, group_member):
        table_state = self.ui.led_table.table_state
        for coors in group_member:
            if table_state[coors[0]][coors[1]]:
                return True

        return False

    def min_num(self, arr):
        min_ = 10000
        for i in arr:
            if i < min_ and i != 0:
                min_ = i

        return min_

    def find_cover_color_coors(self, list_group, time_cur, coors_list, coors_list_red):
        o_led_table = self.ui.led_table
        time_threshold = self.blue_hide_max_time
        tmp_color_red3 = [
         Color.RED] * 3
        for group in list_group:
            if group.type == Setting.FLOOR_LIGHT and group.speed == 0:
                if group.start_time_sec + time_threshold < time_cur < group.end_time_sec:
                    if group.color in [o_led_table.safe_color, tmp_color_red3]:
                        if group.color == [Color.RED] * 3:
                            for cell in group.start_member:
                                i = round(cell[0])
                                j = round(cell[1])
                                if o_led_table.plus_table[i][j] is not None:
                                    coors_list_red.append((i, j))

            else:
                for cell in group.start_member:
                    i = round(cell[0])
                    j = round(cell[1])
                    if o_led_table.plus_table[i][j] is not None or o_led_table.deduct_table[i][j]:
                        coors_list.append((i, j))

    def color_cover_over_times_prompt(self, dict_group, time_cur):
        o_led_table = self.ui.led_table
        time_threshold = self.blue_hide_max_time
        list_group = dict_group.values()
        self.list_hidden_coors.clear()
        self.list_hidden_colors.clear()
        coors_list = []
        coors_list_red = []
        self.find_cover_color_coors(list_group, time_cur, coors_list, coors_list_red)
        tmp_hidden_color = self.color_array + [Color.DEDUCT_COLOR]
        for group in list_group:
            if group.type == Setting.FLOOR_LIGHT and group.speed == 0:
                if group.start_time_sec + time_threshold < time_cur < group.end_time_sec:
                    if group.color in tmp_hidden_color:
                        for cell in group.start_member.copy():
                            i = cell[0]
                            j = cell[1]
                            if not (self.table_cover_show[i][j] or o_led_table.safe_table[i][j]):
                                if o_led_table.red_table[i][j]:
                                    if cell in coors_list:
                                        self.list_hidden_coors.append(cell)
                                        self.list_hidden_colors.append(group.color)
                                if cell in coors_list_red:
                                    group.start_member.remove(cell)

    def color_cover_over_times_disappear(self, dict_group, time_cur):
        o_led_table = self.ui.led_table
        time_threshold = self.blue_hide_max_time
        list_group = dict_group.values()
        coors_list = []
        coors_list_red = []
        self.find_cover_color_coors(list_group, time_cur, coors_list, coors_list_red)
        coors_list_all = coors_list + coors_list_red
        tmp_hidden_color = self.color_array + [Color.DEDUCT_COLOR]
        for group in list_group:
            if group.type == Setting.FLOOR_LIGHT and group.speed == 0:
                if group.start_time_sec + time_threshold < time_cur < group.end_time_sec:
                    if group.color in tmp_hidden_color:
                        for cell in group.start_member.copy():
                            i = round(cell[0])
                            j = round(cell[1])
                            if not o_led_table.other_color_table[i][j] or o_led_table.red_table[i][j] or o_led_table.safe_table[i][j]:
                                if cell in coors_list_all:
                                    group.start_member.remove(cell)

    def vary_with_color_state(self, dict_group, time_pass, total_pass):
        try:
            led_table = self.ui.led_table
            row = led_table.row
            col = led_table.col
            table_state = led_table.table_state
            last_trigger_span = led_table.last_trigger_span
            red_tb = led_table.red_table
            safe_tb = led_table.safe_table
            for i in range(row):
                for j in range(col):
                    nums = self.position_info[i][j][1]
                    if nums > 1:
                        list_group = self.position_info[i][j][0]
                        for group in list_group:
                            group.start_member.remove((i, j))

                    if nums > 0:
                        self.position_info[i][j][0].clear()
                        self.position_info[i][j][1] = 0

            group_items = dict_group.items()
            for key, group in group_items:
                if group.start_time_sec <= self.total_pass <= group.end_time_sec:
                    if group.type == Setting.FLOOR_LIGHT:
                        if group.color == [Color.RED] * 3:
                            for coors in group.start_member.copy():
                                i = coors[0]
                                j = coors[1]
                                if table_state[i][j] and total_pass - last_trigger_span[i][j] > self.trigger_span:
                                    last_trigger_span[i][j] = total_pass
                                    self.life_value -= 1
                                    audio.Audio().play(self.audio_shoot_off)
                                    group = LedGroup([(i, j)], color=(Color.RED))
                                    self.list_group_blink.append(group)

                        elif group.color == Color.DEDUCT_COLOR:
                            for coors in group.start_member.copy():
                                i = coors[0]
                                j = coors[1]
                                if table_state[i][j]:
                                    if not red_tb[i][j]: self.life_value -= 1
                                    audio.Audio().play(self.audio_shoot_off)
                                    group.start_member.remove(coors)
                                    if safe_tb[i][j]:
                                        group_tmp = LedGroup([(i, j)], color=(group.color), life_period=(self.hidn_tread_show_time),
                                          is_living=True)
                                        self.list_hidden_tread_group.append(group_tmp)
                                    else:
                                        group = LedGroup([(i, j)], color=(group.color))
                                        self.list_group_blink.append(group)

                        elif group.color != led_table.safe_color:
                            for coors in group.start_member.copy():
                                if table_state[coors[0]][coors[1]]:
                                    tmp_bool = True
                                    for i in range(self.player_nums):
                                        if group.color == self.color_array[i]:
                                            tmp_bool = red_tb[coors[0]][coors[1]] or False
                                            self.color_scode[i] += 1
                                            self.total_scode[i] += 1
                                            group.start_member.remove(coors)
                                            audio.Audio().play(self.audio_shoot_on)
                                            if safe_tb[coors[0]][coors[1]]:
                                                group_tmp = LedGroup([(coors[0], coors[1])], color=(group.color), life_period=(self.hidn_tread_show_time),
                                                  is_living=True)
                                                self.list_hidden_tread_group.append(group_tmp)
                                            break

                                    if tmp_bool:
                                        audio.Audio().play(self.audio_shoot_off)
                                        group = LedGroup([(coors[0], coors[1])], color=(group.color))
                                        self.list_group_blink.append(group)

        except:
            logger.error(traceback.format_exc())
            return False

    def game_info_realtime(self, time_pass, time_order=False):
        if time_pass >= 0.3:
            logger.warning("bad game frame frequency:" + str(time_pass))
        total_pass = self.total_pass
        if not time_order:
            self.game_record_rt.game_blood = self.life_value
        self.game_record_rt.game_time_left -= time_pass
        if self.life_value <= 0 or total_pass > self.cur_game_time or self.game_record_rt.game_time_left <= 0:
            if not time_order:
                if self.life_value <= 0:
                    self.game_record_rt.game_result = 0
                else:
                    if total_pass > self.cur_game_time:
                        self.game_record_rt.game_result = 1
                    else:
                        self.game_record_rt.game_result = 2
            self.ui.led_table.clear_led_table()
            led_control.draw_led_color(None, self.ui.led_table.led_table)
            logger.info("editor2 game over")
            return False
        return True

    def stop_running(self):
        self.running_state = False

    def draw_code_group(self, time_pass):
        color_table = self.ui.led_table.led_table
        # Decompiler inverted this condition via De Morgan's law.
        # Original: if breath groups exist (and no hidden tiles active), animate them.
        if len(self.list_group_breath) > 0:
            group = self.list_group_breath[0]
            group_state = self.get_group_state(group.member)
            if group_state and group.trigger_span_tm > self.trigger_span:
                group.trigger_span_tm = 0
                self.life_value -= 1
                for i in range(self.player_nums):
                    self.color_scode[i] -= self.prompt_cost
                    self.total_scode[i] -= self.prompt_cost

                group = LedGroup((group.member.copy()), color=(group.color))
                self.list_group_blink.append(group)
                for idx in range(len(self.list_hidden_coors) - 1, -1, -1):
                    coors = self.list_hidden_coors[idx]
                    if not self.table_cover_show[coors[0]][coors[1]]:
                        group = LedGroup([coors], color=(self.list_hidden_colors[idx]), life_period=(self.prompt_time), is_living=True)
                        self.list_hidden_group.append(group)
                        self.list_hidden_coors.pop(idx)
                        self.list_hidden_colors.pop(idx)
                        self.table_cover_show[coors[0]][coors[1]] = True
            else:
                group.breath(time_pass)
                group.draw(color_table, group.breath_color)
        for group in self.list_hidden_tread_group.copy():
            if group.is_living:
                group.vary(time_pass)
                group.draw(color_table, group.color)
            else:
                self.list_hidden_tread_group.remove(group)

        for group in self.list_hidden_group.copy():
            group_state = self.get_group_state(group.member)
            if group_state:
                self.list_hidden_group.remove(group)
                blink_group = LedGroup((group.member.copy()), color=(group.color))
                self.list_group_blink.append(blink_group)
                for coors in group.member:
                    self.table_cover_show[coors[0]][coors[1]] = False

            elif group.is_living:
                group.vary(time_pass)
                group.draw(color_table, group.color)
            else:
                self.list_hidden_group.remove(group)
                for coors in group.member:
                    self.table_cover_show[coors[0]][coors[1]] = False

        for group_blink in self.list_group_blink.copy():
            if group_blink.is_exist:
                group_blink.blink(time_pass)
                group_blink.draw(color_table, group_blink.blink_color)
            else:
                self.list_group_blink.remove(group_blink)

    def draw_init_editor_group(self, dict_group):
        o_led_table = self.ui.led_table
        for key, group in dict_group.items():
            if group.start_time_sec <= self.total_pass <= group.end_time_sec:
                if group.type == Setting.FLOOR_LIGHT:
                    o_led_table.set_color_table_by_set_cell(group.start_member, group.color)
                else:
                    if group.type == Setting.WALL_LIGHT:
                        try:
                            for index in group.start_member:
                                o_led_table.get_wall_light_arr()[index] = group.color

                        except:
                            logger.error("running update wall button light arr {}", traceback.format_exc())

                o_led_table.redraw_led_table_default(line=(self.wall_line), draw_canvas=False)

    def correct_dc_gp_color_and_player_nums(self, dict_group):
        list_group_color = []
        for group in dict_group.values():
            if group.color not in list_group_color:
                list_group_color.append(group.color)

        color_useful_nums = 0
        for color in self.color_array.copy():
            if color in list_group_color:
                color_useful_nums += 1

        self.player_nums = color_useful_nums

    def record_position_info(self, group):
        for cell in group.start_member:
            self.position_info[cell[0]][cell[1]][0].append(group)
            self.position_info[cell[0]][cell[1]][1] += 1

    def check_player_color(self, dict_group, list_player_color):
        list_group_color = []
        for group in dict_group.values():
            if group.color not in list_group_color:
                list_group_color.append(group.color)

        for color in self.color_array.copy():
            if color in list_group_color:
                list_player_color.append(color)

    def goal_led_group_start_time_list(self, dict_group):
        list_start_time_goal_group = []
        list_start_time_goal_group2 = []
        for key, group in dict_group.items():
            if group.type == Setting.WALL_LIGHT:
                list_start_time_goal_group.append((group.start_time_sec, group.color))
            elif group.type == Setting.SCREEN_LIGHT:
                list_start_time_goal_group2.append((group.start_time_sec, group.color))

        self.list_start_time_goal_group = sorted(list_start_time_goal_group, key=(lambda x: x[0]))
        self.list_start_time_goal_group2 = sorted(list_start_time_goal_group2, key=(lambda x: x[0]))
        # True when the game data defines two independent goal-color streams.
        self._two_color_mode = len(self.list_start_time_goal_group2) > 0
        logger.info("goal_led_group_start_time_list: {} WALL_LIGHT entries, {} SCREEN_LIGHT entries, two_color={}",
                    len(self.list_start_time_goal_group), len(self.list_start_time_goal_group2), self._two_color_mode)

    def frame_auto_jump(self, dict_group):
        next_goal_group_start = 3600
        for member in self.list_start_time_goal_group.copy():
            start_time, color = member
            if start_time < self.total_pass:
                self.list_start_time_goal_group.remove(member)
                self.ui.led_table.goal_color = color
                self.color_array[0] = color
            else:
                next_goal_group_start = start_time
                break

        next_goal_group_start2 = 3600
        for member in self.list_start_time_goal_group2.copy():
            start_time, color = member
            if start_time < self.total_pass:
                self.list_start_time_goal_group2.remove(member)
                self.ui.led_table.goal_color2 = color
                self.color_array[1] = color
            else:
                next_goal_group_start2 = start_time
                break

        group_items = dict_group.items()
        b_has_color1 = False
        b_has_color2 = False
        for key, value in group_items:
            group = value
            if group.type == Setting.FLOOR_LIGHT and len(group.start_member) > 0 and group.color == self.ui.led_table.goal_color:
                if group.start_time_sec <= self.total_pass < group.end_time_sec:
                    next_goal_group_start = self.total_pass
                    b_has_color1 = True
                    break
                if self.total_pass < group.start_time_sec < next_goal_group_start:
                    next_goal_group_start = group.start_time_sec

        for key, value in group_items:
            group = value
            if group.type == Setting.FLOOR_LIGHT and len(group.start_member) > 0 and group.color == self.ui.led_table.goal_color2:
                if group.start_time_sec <= self.total_pass < group.end_time_sec:
                    next_goal_group_start2 = self.total_pass
                    b_has_color2 = True
                    break
                if self.total_pass < group.start_time_sec < next_goal_group_start2:
                    next_goal_group_start2 = group.start_time_sec

        if self._two_color_mode:
            # Two-color arena: both players must have an active goal simultaneously.
            self.total_pass = max(next_goal_group_start, next_goal_group_start2)
            has_active = b_has_color1 and b_has_color2
        else:
            # Single-color mode (no SCREEN_LIGHT groups in game data).
            self.total_pass = next_goal_group_start
            has_active = b_has_color1

        result = has_active or self.total_pass == 3600
        if result:
            return True
        return False

    def running(self, dict_group, running_order):
        cur_game_fragment = self.parent_game_running.cur_game_fragment
        self.audio_shoot_on = cur_game_fragment.blue_tread
        self.audio_shoot_off = cur_game_fragment.red_tread
        logger.info("editor game2 running: running_order={} cur_game_time={:.1f}s game_time={}min time_left={:.1f}s",
                    running_order, self.cur_game_time, self.game_time, self.game_record_rt.game_time_left)
        self.running_state = True
        self.total_pass = 0
        o_led_table = self.ui.led_table
        self.last_time = time.time()
        list_player_color = []
        self.check_player_color(dict_group, list_player_color)
        len_list_player_color = len(list_player_color)
        self.goal_led_group_start_time_list(dict_group)
        while self.running_state and self.circle_game:
            current_time = time.time()
            time_pass = current_time - self.last_time
            self.last_time = current_time
            self.total_pass += time_pass
            if not running_order:
                # Frame-jump mode: skip to next active goal group time.
                # The 'elif not ret: continue' in the decompiled code was
                # wrongly placed at the outer level — it must be inside this
                # branch so that running_order=True never hits continue.
                ret = self.frame_auto_jump(dict_group)
                if not ret:
                    time.sleep(0.005)  # prevent CPU spin while waiting for next goal
                    continue
            o_led_table.clear_led_table()
            for key, group in dict_group.copy().items():
                if group.start_time_sec <= self.total_pass <= group.end_time_sec:
                    change = 0
                    last_speed = 0
                    if group.speed != 0:
                        last_speed = 1 / group.speed * self.game_level_speed
                        change = last_speed * time_pass
                        # First-frame precision: clamp to actual elapsed time within this group.
                        tmp_time = self.total_pass - group.start_time_sec
                        if 0 < tmp_time < time_pass:
                            change = tmp_time * last_speed
                    # Always accumulate fractional movement (was inside dead elif branch).
                    group.move_distance += change
                    if group.move_distance < 1:
                        # Group has not yet accumulated a full step — just colour it.
                        if group.type == Setting.FLOOR_LIGHT:
                            o_led_table.set_color_table_by_set_cell(group.start_member, group.color)
                            if group.speed == 0 and self.total_pass - group.start_time_sec > self.blue_hide_max_time and group.color in self.color_array:
                                self.record_position_info(group)
                                continue
                    else:
                        # Consume one step and move the group.
                        group.move_distance -= 1
                        direction_current, set_cell_current = self.game_util.deal_all_direction(group)
                        group.start_member = set_cell_current
                        group.direct = direction_current
                        dict_group[key] = group
                        if group.type == Setting.FLOOR_LIGHT:
                            o_led_table.set_color_table_by_set_cell(group.start_member, group.color)
                            if group.speed == 0 and self.total_pass - group.start_time_sec > self.blue_hide_max_time:
                                self.record_position_info(group)
                else:
                    if self.total_pass >= group.end_time_sec:
                        dict_group.pop(key)

            if self.cover_action == "disappear":
                self.color_cover_over_times_disappear(dict_group, self.total_pass)
            else:
                self.color_cover_over_times_prompt(dict_group, self.total_pass)
            self.vary_with_color_state(dict_group, time_pass, self.total_pass)
            o_led_table.redraw_led_table_default(draw_canvas=False)
            self.draw_code_group(time_pass)
            # Decompiler bug: screen_mouse_click_state_get() is a method on self,
            # not on o_led_table.
            self.screen_mouse_click_state_get()
            if Setting.USE_SERIAL_HD:
                self.parent_game_running.draw_hw_led_color_inc_wal(self.ui.led_table)
            else:
                o_led_table.draw_led_color()
            if not self.game_info_realtime(time_pass, running_order):
                self.stop_running()
            self.game_record_rt.game_info2 = self.color_array
            self.ui.update_ui(self.game_record_rt, time_pass)
            if Setting.USE_SERIAL_HD:
                self.parent_game_running.get_hw_led_state_inc_wal(self.ui.led_table)

            # ── Frame-rate cap: target 30 FPS ─────────────────────────────────
            _frame_elapsed = time.time() - current_time
            _sleep = (1.0 / 30.0) - _frame_elapsed
            if _sleep > 0.001:
                time.sleep(_sleep)
            # Pump Tkinter idle tasks so canvas labels (score, timer) repaint
            # even while this blocking loop owns the main thread.
            try:
                self.ui.root.update_idletasks()
            except Exception:
                pass

    def play_running(self, game_unzip_dir, setting):
        led_table_obj = self.ui.led_table
        self.game_util.unzipfile(game_unzip_dir)
        logger.info("game_unzip_dir")
        game_unzip_dir = os.path.splitext(game_unzip_dir)[0]
        self.cur_game_name = game_unzip_dir
        self.ui.update_game_name_ui(os.path.basename(game_unzip_dir).split(".")[0])
        for game_folder in os.listdir(game_unzip_dir):
            logger.info(game_folder)
            game_end = None
            dict_group_end = None
            game_end_dir = None
            if self.circle_game:
                game, dict_group = self.game_util.read_game_and_group(game_unzip_dir, game_folder, setting, game_type=2)
                self.cur_game_time = self.game_util.get_max_end_time_in_all_group(dict_group)
                game_folder_path = game_unzip_dir + "/" + game_folder
                color_tmp = game.safe_color
                self.cover_color = (Color.GREEN, color_tmp, Color.RED)
                self.no_score_color = (Color.GREEN, color_tmp, Color.RED, Color.BLACK)
                self.ui.led_table.safe_color = color_tmp
                if game.cover_action:
                    self.cover_action = "prompt"
                else:
                    self.cover_action = "disappear"
                self.parent_game_running.game_music_init(setting, game_folder_path, game)
                if game.play_order:
                    loops = 0
                else:
                    loops = -1
                # game_time_left counts down from game_time (minutes) × 60 seconds.
                # It starts at 0 in GameRecordRT so we must set it here before the loop.
                self.game_record_rt.game_time_left = self.game_time * 60
                self.parent_game_running.music("introduce", True, self.ui.root, loops)
                self.running(dict_group, game.play_order)
                self.parent_game_running.music("stop")
                if self.circle_game:
                    if self.game_record_rt.game_result == 0:
                        self.life_value = 1
                        game_end, dict_group_end, game_end_dir = self.game_util.read_game_parameter_game_frag(os.path.join(game_unzip_dir + "/" + game_folder, "game_file"), game.clap_light, setting)
                    else:
                        game_end, dict_group_end, game_end_dir = self.game_util.read_game_parameter_game_frag(os.path.join(game_unzip_dir + "/" + game_folder, "game_file"), game.game_accomplished, setting)
            if game_end is not None:
                if dict_group_end is not None:
                    self.cur_game_time = self.game_util.get_max_end_time_in_all_group(dict_group_end)
                    self.parent_game_running.music("introduce", True, self.ui.root, loops)
                    self.running(dict_group_end, True)
                    self.parent_game_running.music("stop")
                if game.play_order or self.game_record_rt.game_result != 0 and self.game_record_rt.game_result != 3:
                    GameFragmentRst(self, 0)

        self.update_draw_led_table_end_of_play()
        self.game_util.remove_unzipfile(game_unzip_dir)
        logger.info("EditorGame2 end play_running")

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui/gui_editor_game2.pyc
