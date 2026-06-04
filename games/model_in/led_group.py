# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: model_in\led_group.py


from model.setting import Color

class LedGroup:
    BLINK_TIME = 3
    BLINK_FREQUENCE = 0.1
    BREATH_SECOND = 2

    @staticmethod
    def _normalise_color(color):
        """Accept either a bare (R,G,B) tuple or a 3-ring list/tuple of RGB values
        and always return a plain list of 3 RGB lists, safe to call .copy() on."""
        if not color:
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # Bare (R,G,B) scalar — expand to three identical rings
        if not isinstance(color[0], (list, tuple)):
            ring = list(color)
            return [ring, ring[:], ring[:]]
        return [list(c) for c in color]

    def __init__(self, member=[], life_period=0, direct="no", speed=0, color=[Color.BLACK] * 3, activity_area=[
 (0, 15), (0, 25)], is_living=False):
        self.member = member
        self.life_period = life_period
        self.direct = direct
        self.speed = speed
        self.living_time = 0
        color = LedGroup._normalise_color(color)
        self.color = color.copy()
        self.move_distance = 0
        self.activity_area = activity_area
        self.is_living = is_living
        self.is_exist = True
        self.trigger_span_tm = 10
        self.blink_nums = 0
        self.blink_frequency_has_pass = 0
        self.switch = True
        self.blink_color = color.copy()
        self.breath_color = color.copy()
        self.breath_color_float = color.copy()
        self.breath_switch = [True, True, True]

    def set_color(self, color=[
 Color.WHITE] * 3):
        color = LedGroup._normalise_color(color)
        self.color = color.copy()
        self.blink_color = color.copy()
        self.breath_color = color.copy()
        self.breath_color_float = color.copy()
        self.breath_switch = [True, True, True]

    def is_shoot(self):
        return

    def vary_DECOMPILE_ERROR(self, *args):
        pass  # decompiler parse error

    def end(self):
        self.blink_color = [
         Color.BLACK] * 3
        self.member.clear()
        self.time_has_pass = 0
        self.blink_frequency_has_pass = 0
        self.switch = False
        self.is_exist = False
        return False

    def blink(self, time_pass_last):
        if self.blink_nums < LedGroup.BLINK_TIME:
            self.blink_frequency_has_pass += time_pass_last
            if self.blink_frequency_has_pass > LedGroup.BLINK_FREQUENCE:
                self.blink_frequency_has_pass = 0
                if not self.switch:
                    self.blink_color = []
                else:
                    self.blink_color = self.color
                    self.blink_nums += 1
                self.switch = not self.switch
            ret = True
        else:
            self.blink_color = self.color
            ret = self.end()
        return ret

    def draw(self, table_color, color):
        for coors in self.member:
            table_color[coors[0]][coors[1]] = color

    def breath_old(self, time_pass):
        self.trigger_span_tm += time_pass
        color_g = self.breath_color[0]
        if self.breath_switch:
            color_nums = 253 * (time_pass / LedGroup.BREATH_SECOND)
        else:
            color_nums = -253 * (time_pass / LedGroup.BREATH_SECOND)
        color_g += color_nums
        color_b = self.breath_color[2]
        color_b += color_nums
        if color_g > 253:
            color_g = 253
            self.breath_switch = False
        else:
            if color_g < 50:
                color_g = 50
                self.breath_switch = True
        if color_b > 253:
            color_b = 253
        if color_b < 50:
            color_b = 50
        self.breath_color = (int(color_g), self.breath_color[1], int(color_b))

    def breath(self, time_pass):
        self.trigger_span_tm += time_pass
        percentage = time_pass / LedGroup.BREATH_SECOND
        for k in range(3):
            idx = 0
            for color_ in self.color[k]:
                if color_ > 0:
                    break
                idx += 1

            idx_0 = idx
            idx_1 = (idx + 1) % 3
            idx_2 = (idx + 2) % 3
            color_1 = self.breath_color_float[k][idx_0]
            color_2 = self.breath_color_float[k][idx_1]
            color_3 = self.breath_color_float[k][idx_2]
            if self.breath_switch[k]:
                color_1 -= self.color[k][idx_0] * percentage
                color_2 -= self.color[k][idx_1] * percentage
                color_3 -= self.color[k][idx_2] * percentage
            else:
                color_1 += self.color[k][idx_0] * percentage
                color_2 += self.color[k][idx_1] * percentage
                color_3 += self.color[k][idx_2] * percentage
            if color_1 < 0:
                color_1 = 0
                self.breath_switch[k] = False
            else:
                if color_1 > self.color[k][idx_0]:
                    color_1 = self.color[k][idx_0]
                    self.breath_switch[k] = True
            if color_2 < 0:
                color_2 = 0
            elif color_2 > self.color[k][idx_1]:
                color_2 = self.color[k][idx_1]
            if color_3 < 0:
                color_3 = 0
            else:
                if color_3 > self.color[k][idx_2]:
                    color_3 = self.color[k][idx_2]
                tmp_arr = [0, 0, 0]
                tmp_arr[idx_0] = round(color_1)
                tmp_arr[idx_1] = round(color_2)
                tmp_arr[idx_2] = round(color_3)
                tmp_arr2 = [0, 0, 0]
                tmp_arr2[idx_0] = color_1
                tmp_arr2[idx_1] = color_2
                tmp_arr2[idx_2] = color_3
                self.breath_color[k] = tuple(tmp_arr)
                self.breath_color_float[k] = tuple(tmp_arr2)
# file /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/model_in/led_group.pyc
# Deparsing stopped due to parse error

