# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: input_listener.py
from pynput import keyboard, mouse

class InputListener:

    def __init__(self, partial=None):
        mouse_listener = mouse.Listener(on_click=(self.on_click), on_scroll=(self.on_scroll))
        self.mouse_listener = mouse_listener
        mouse_listener.start()
        keyboard_listener = keyboard.Listener(on_press=(self.on_press))
        self.keyboard_listener = keyboard_listener
        keyboard_listener.start()
        self.partial = partial

    def stop(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def on_move(self, x, y):
        return

    def on_click(self, x, y, button, pressed):
        self.partial()

    def on_scroll(self, x, y, dx, dy):
        self.partial()

    def on_press(self, key):
        self.partial()

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/util/input_listener.pyc
