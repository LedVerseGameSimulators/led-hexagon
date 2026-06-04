# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: model_in\game_record_rt.py
import time
from model.setting import Setting

class GameRecordRT:

    def __init__(self):
        self.game_time_pass = 0
        self.game_time_start = 0
        self.game_time_left = 0
        self.game_scode = 0
        self.game_scode_left = 0
        self.game_scode_right = 0
        self.game_blood = 0
        self.game_blood_left = 0
        self.game_blood_right = 0
        self.game_result = 2
        self.game_info = None
        self.game_info2 = None   # used by EditorGame2 for colour-array broadcast
        self.game_state = Setting.GAME_IDLE
        self.running_to_obj = None
        self.running_to_flag = 0

    def reset(self, game_time_pass=None, game_scode=None, game_scode_left=None, game_scode_right=None, running_to_obj=None):
        self.game_time_start = 0
        if game_time_pass is not None:
            self.game_time_pass = game_time_pass
        if game_scode is not None:
            self.game_scode = game_scode
        if game_scode_left is not None:
            self.game_scode_left = game_scode_left
        if game_scode_right is not None:
            self.game_scode_right = game_scode_right
        self.game_result = 2
        self.game_time_left = 0
        self.game_info = None
        self.game_info2 = None
        self.running_to_obj = running_to_obj

    def get_game_time_pass(self):
        if self.game_time_start > 0:
            self.game_time_pass = (time.time() - self.game_time_start) / 60
        else:
            self.game_time_pass = 0
        return self.game_time_pass

    def start_game_time(self):
        if self.game_time_start == 0:
            self.game_time_start = time.time()

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/model_in/game_record_rt.pyc
