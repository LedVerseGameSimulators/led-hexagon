# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: life_value_calculation.py

import shelve, time
from audio_play import audio
from loguru import logger
from model.setting import Color, Setting
from model_in.led_group import LedGroup

class LifeValueCalculation:
    ALL_LIFE_VALUE = 10
    ONE_LIFE_VALUE = 1
    ONE_SCODE_VALUE = 1

    def __init__(self, row, col, one_life_value=1, table_state=None, table_color=None, audio_name_sub='./audio/bomb.mp3', audio_name_add='./audio/prompt.mp3', game_name=None, all_life_value=10, scode_init=0, scode_left=0, scode_right=0):
        time_now = time.time()
        self.table_tread_time = [[time_now] * col for _ in range(row)]
        self.table_tread_duration_time = [[0] * col for _ in range(row)]
        self.arr_count_between_time = [10] * (row + col)
        self.table_count_time = [[0] * col for _ in range(row)]
        self.row = row
        self.col = col
        LifeValueCalculation.ALL_LIFE_VALUE = all_life_value
        try:
            f = shelve.open("./setting/debug_parameter")
            self.duration_time = float(f.get("tread_red_time"))
            self.TIME = float(f.get("life_value_count_time"))
            f.close()
        except:
            self.duration_time = 0.1
            self.TIME = 1.0

        logger.warning("踩红灯持续时间{}, 掉血时间间隔{}", self.duration_time, self.TIME)
        self.one_life_value = one_life_value
        self.table_state = table_state
        self.table_color = table_color
        self.audio_name_sub = audio_name_sub
        self.audio_name_add = audio_name_add
        self.life_value = LifeValueCalculation.ALL_LIFE_VALUE
        self.scode_value = scode_init
        self.last_value_dec_time = time.time()
        self.life_value_left = 0
        self.life_value_right = 0
        self.scode_value_left = scode_left
        self.scode_value_right = scode_right

    def calculation_old_DECOMPILE_ERROR(self, *args):
        pass  # decompiler parse error

    def calculation(self, life_value, color, table_state, table_color, audio_name='./audio/bomb.mp3', state_update=None):
        time_now = time.time()
        if state_update is None:
            for i in range(self.row):
                for j in range(self.col):
                    time_last = self.table_tread_time[i][j]
                    time_bettwn = time_now - time_last
                    if table_state[i][j] and table_color[i][j] in color and time_bettwn > self.TIME:
                        life_value -= self.one_life_value
                        self.table_tread_time[i][j] = time_now
                        audio.Audio().play(audio_name)

        else:
            for i in range(self.row):
                for j in range(self.col):
                    time_last = self.table_tread_time[i][j]
                    time_bettwn = time_now - time_last
                    if table_state[i][j] and table_color[i][j] in color and time_bettwn > self.TIME and state_update[i][j]:
                        life_value -= self.one_life_value
                        self.table_tread_time[i][j] = time_now
                        audio.Audio().play(audio_name)

        return life_value

    def calculation_one_second_snake(self, life_value, color, table_state, table_color, audio_name='./audio/snake/bomb.mp3', time_passed=0, min_time=None):
        if min_time is not None:
            min_time = min_time
        else:
            min_time = self.duration_time
        time_now = time.time()
        time_bettwn = time_now - self.last_value_dec_time
        for i in range(self.row):
            for j in range(self.col):
                if table_state[i][j]:
                    if table_color[i][j] in color:
                        self.table_tread_duration_time[i][j] += time_passed
                    else:
                        self.table_tread_duration_time[i][j] = 0
                    if self.table_tread_duration_time[i][j] > min_time and time_bettwn > self.TIME:
                        life_value -= self.one_life_value
                        audio.Audio().play(audio_name)
                        self.last_value_dec_time = time_now
                        return life_value

        return life_value

    def calculation_editor_group_DECOMPILE_ERROR(self, *args):
        pass  # decompiler parse error

    def calculation_one_second_250513(self, life_value, color, table_state, table_color, audio_name=None, audio_scode=None, time_passed=0, min_time=None, group_blink=None, no_score_color=[]):
        if min_time is not None:
            min_time = min_time
        else:
            min_time = self.duration_time
        time_now = time.time()
        time_bettwn = time_now - self.last_value_dec_time
        for i in range(self.row):
            for j in range(self.col):
                if table_color[i][j] == Color.TEST_COLOR:
                    logger.debug("state{}", table_state[i][j])
                if table_state[i][j] and table_color[i][j] in color:
                    self.table_tread_duration_time[i][j] += time_passed
                else:
                    self.table_tread_duration_time[i][j] = 0
                self.table_count_time[i][j] += time_passed
                if table_state[i][j]:
                    if table_color[i][j] not in no_score_color:
                        self.scode_value += self.ONE_SCODE_VALUE
                        audio.Audio().play(audio_scode)
                    if self.table_tread_duration_time[i][j] > min_time and self.table_count_time[i][j] > self.TIME:
                        self.life_value -= self.one_life_value
                        self.scode_value -= self.ONE_SCODE_VALUE
                        audio.Audio().play(audio_name)
                        self.last_value_dec_time = time_now
                        self.table_count_time[i][j] = 0
                        if group_blink is not None:
                            group_blink.add_led_blink([(i, j)])

    def calculation_one_second_wall_light_dict_group(self, arr_state, audio_name='./audio/bomb.mp3', dict_group=None, total_pass=0):
        for key, group in dict_group.items():
            if group.color == Color.BLUE and group.type == Setting.WALL_LIGHT:
                start_time = group.start_time_sec
                end_time = group.end_time_sec
                set_cell = group.start_member
                if set_cell:
                    if start_time < total_pass < end_time:
                        for cell in set_cell.copy():
                            if arr_state[cell]:
                                self.scode_value += self.ONE_SCODE_VALUE
                                audio.Audio().play(audio_name)
                                set_cell.remove(cell)

    def calculation_one_second_wall_light_old(self, life_value, color, arr_state, arr_color, audio_name='./audio/bomb.mp3', time_passed=0, min_time=None, screen_bool=False):
        for j in range(len(arr_state)):
            if arr_state[j] and arr_color[j] == Color.BLUE:
                self.scode_value += self.ONE_SCODE_VALUE
                arr_color[j] = Color.BLACK
                audio.Audio().play(audio_name)

    def calculates_floor(self, dict_group, led_table, list_color_action=[]):
        list_color = list_color_action[0]
        list_score = list_color_action[1]
        list_life = list_color_action[2]
        list_action = list_color_action[3]
        table_state = led_table.get_state_table()
        last_trigger_span = led_table.last_trigger_span
        for key, group in dict_group.items():
            if group.start_time_sec <= self.total_pass <= group.end_time_sec:
                if group.type == Setting.FLOOR_LIGHT and group.color in list_color:
                    for coors in group.start_member.copy():
                        if table_state[coors[0]][coors[1]]:
                            idx = list_color.index(group.color)
                            if not list_action[idx]:
                                self.life_value += list_life[idx]
                                self.scode_value += list_score[idx]
                                group.start_member.remove(coors)
                            elif last_trigger_span[coors[0]][coors[1]] > self.TIME:
                                last_trigger_span[coors[0]][coors[1]] = 0.0
                                self.life_value += list_life[idx]
                                self.scode_value += list_score[idx]

    def calculation_all(self, setting, led_table, audio_name="", audio_scode="", time_passed=0, group_blink=[]):
        return

    def min_num(self, arr):
        min_ = 10000
        for i in arr:
            if i < min_ and i != 0:
                min_ = i

        return min_

    def calculation_one_second_screen_light(self, life_value, color, arr_state, arr_color, arr_text, audio_name='./audio/bomb.mp3', time_passed=0, min_time=None, screen_bool=False):
        arr_tmp = arr_text.copy()
        min_num_in_text = self.min_num(arr_tmp)
        for j in range(len(arr_state)):
            if arr_state[j] and arr_color[j] == Color.BLUE:
                if arr_tmp[j] == min_num_in_text:
                    self.scode_value += self.ONE_SCODE_VALUE
                    audio.Audio().play(self.audio_name_add)
                    arr_tmp.remove(min_num_in_text)
                    min_num_in_text = self.min_num(arr_tmp)
                else:
                    self.life_value -= self.one_life_value
                    self.scode_value -= self.ONE_SCODE_VALUE
                    audio.Audio().play(audio_name)

    def calculation_one_second_screen_light_dict_group(self, arr_state, arr_text, audio_name='./audio/bomb.mp3', audio_scode=None, time_passed=0, dict_group=None, total_pass=0):
        arr_tmp = arr_text.copy()
        min_num_in_text = self.min_num(arr_tmp)
        for key, group in dict_group.items():
            if group.color == Color.BLUE and group.type == Setting.WALL_LIGHT:
                start_time = group.start_time_sec
                end_time = group.end_time_sec
                set_cell = group.start_member
                if set_cell is not None and total_pass > start_time and total_pass < end_time:
                    for cell in set_cell.copy():
                        self.arr_count_between_time[cell] += time_passed
                        if arr_state[cell]:
                            if arr_text[cell] == min_num_in_text:
                                self.scode_value += self.ONE_SCODE_VALUE
                                audio.Audio().play(audio_scode)
                                arr_tmp.remove(min_num_in_text)
                                min_num_in_text = self.min_num(arr_tmp)
                                set_cell.remove(cell)
                                arr_text[cell] = 0
                                self.arr_count_between_time[cell] = 0
                            else:
                                if self.arr_count_between_time[cell] > self.TIME:
                                    self.life_value -= self.one_life_value
                                    self.scode_value -= self.ONE_SCODE_VALUE
                                    self.arr_count_between_time[cell] = 0
                                    audio.Audio().play(audio_name)
                                logger.debug("group remove pos", cell)
                                logger.debug("wall_light_state[cell] is true", cell)
                                logger.debug(set_cell)

        for key, group in dict_group.items():
            if group.type == Setting.SCREEN_LIGHT:
                start_time = group.start_time_sec
                end_time = group.end_time_sec
                set_cell = group.start_member
                if set_cell is not None and total_pass > start_time and total_pass < end_time:
                    for cell in set_cell.copy():
                        if arr_state[cell] and arr_text[cell] == 0:
                            group.text.pop(set_cell.index(cell))
                            set_cell.remove(cell)

    def add_one_scode(self):
        self.scode_value += 1
        audio.Audio().play(self.audio_name_add)
# file /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/game_play/life_value_calculation.pyc
# Deparsing stopped due to parse error

