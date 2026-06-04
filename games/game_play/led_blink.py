# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: led_blink.py


class LedBlink:

    def __init__(self, table, area_coors=[], color_positive=1, color_negative=0):
        self.blink_start = True
        self.blink_times = 4
        self.blink_time_pass = 0
        self.blink_period = 0.1
        self.blink_switch = False
        self.blink_color_positive = color_positive
        self.blink_color_negative = color_negative
        self.blink_cur_color = self.blink_color_negative
        self.area_coors = area_coors
        self.draw_table = table

    def blink_and_disappear(self, time_pass):
        if self.blink_start:
            if self.blink_times > 0:
                self.blink_time_pass += time_pass
                if self.blink_time_pass >= self.blink_period:
                    self.blink_time_pass = 0
                    self.blink_switch = not self.blink_switch
                    self.blink_times -= 1
                if self.blink_switch:
                    self.blink_cur_color = self.blink_color_positive
            else:
                self.blink_cur_color = self.blink_color_negative
        else:
            if self.blink_start:
                if self.blink_times <= 0:
                    self.blink_cur_color = self.blink_color_negative
                    self.blink_start = False
        if self.blink_start:
            self.draw(self.blink_cur_color)

    def draw(self, color):
        for coors in self.area_coors:
            self.draw_table[coors[0]][coors[1]] = color


class LedBlinkGroup:

    def __init__(self, table, color_pos=1, color_neg=0):
        self.group_member = []
        self.draw_table = table
        self.color_pos = color_pos
        self.color_neg = color_neg

    def add_led_blink(self, blink_area_coors):
        led_blink = LedBlink((self.draw_table), blink_area_coors, color_positive=(self.color_pos), color_negative=(self.color_neg))
        self.group_member.append(led_blink)

    def group_blink(self, time_pass):
        for member in self.group_member.copy():
            if member.blink_start:
                member.blink_and_disappear(time_pass)
            else:
                self.group_member.remove(member)

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/game_play/led_blink.pyc
