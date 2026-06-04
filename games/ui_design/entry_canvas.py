# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: ui_design\entry_canvas.py
import subprocess
from tkinter import Canvas, Event
from tkinter.font import Font
from PIL import Image, ImageTk, ImageEnhance

class Entry_Canvas:

    def editable(self, flag):
        self.b_editable = flag

    def __init__(self, canvas, x, y, r_width, r_height, text1, text2, pw_mode=False, d_outline='gray', d_fill='gray', fontsize=15, outlineboder=2, flag='', text3='', image_path='', no_frame_img=False):
        self.canvas = canvas
        self.focus = False
        self.mode = pw_mode
        self.b_editable = True
        self.flag = flag
        self.value = text1
        self.info = str(text1)
        self.label = text3
        self.x1 = x - r_width / 2
        self.y1 = y - r_height / 2
        self.x2 = x + r_width / 2
        self.y2 = y + r_height / 2
        self.info1 = text2
        self.info2 = text2
        self.d_outline = d_outline
        self.d_fill = d_fill
        self.keyboard = None
        self.function_var = None
        self.image_path = image_path
        self.no_frame_img = no_frame_img
        self.create_image_bg(x, y, r_width, r_height)
        self.rec = self.canvas.create_rectangle((self.x1), (self.y1), (self.x2), (self.y2), width=outlineboder, outline=d_outline)
        input_coors_x = x
        input_coors_y = y
        font = Font(family="STKaiti", size=fontsize)
        if text3 != "":
            self.label_txt = self.canvas.create_text((self.x1), y, text=(self.label), font=font, fill=d_fill, anchor="w")
            input_coors_x = self.x1 + font.measure(self.label + ": ")
        self.tex = self.canvas.create_text(input_coors_x, input_coors_y, text=(self.info1), font=font, fill=d_fill)

    def create_image_bg(self, image_x, image_y, type_width, type_height):
        image_bg_id = None
        if self.image_path != "":
            image_title = Image.open(self.image_path)
            image_title = image_title.resize((round(type_width), round(type_height)), Image.LANCZOS)
            self.image_bg = ImageTk.PhotoImage(image_title)
            image_bg_id = self.canvas.create_image(image_x, image_y, image=(self.image_bg), tags="button_image")
        if not self.no_frame_img:
            path_img_bgm_frame = "./photo/new/introduce_rect.png"
            image_title = Image.open(path_img_bgm_frame)
            image_title = image_title.resize((round(type_width), round(type_height)), Image.LANCZOS)
            self.image_bg_frame = ImageTk.PhotoImage(image_title)
            self.image_frame_id = self.canvas.create_image(image_x, image_y, image=(self.image_bg_frame), tags="button_image")
        return image_bg_id

    def _canvas_ok(self) -> bool:
        try:
            return bool(self.canvas.winfo_exists())
        except Exception:
            return False

    def update(self, text):
        if not self._canvas_ok():
            return
        self.value = text
        self.canvas.itemconfig((self.tex), text=text)

    def update_info1(self):
        if not self._canvas_ok():
            return
        self.canvas.itemconfig((self.tex), text=(self.info1))

    def clear(self):
        self.value = ""
        self.info = ""
        if not self._canvas_ok():
            return
        self.canvas.itemconfig((self.tex), text=(self.info1))

    def focus_on(self, color: str):
        if not self._canvas_ok():
            return
        if self.b_editable:
            self.focus = True
            try:
                self.canvas.itemconfig((self.rec), outline=color)
                self.canvas.itemconfig((self.tex), text=(self.info + "|"))
            except Exception:
                pass
            self.display_keyboard()

    def focus_off(self):
        self.focus = False
        if not self._canvas_ok():
            return
        try:
            self.canvas.itemconfig((self.rec), outline=(self.d_outline))
            if self.info == "":
                self.canvas.itemconfig((self.tex), text=(self.info1))
            else:
                self.canvas.itemconfig((self.tex), text=(self.info))
        except Exception:
            pass

    def Focus(self, event_xy, color: str='white', str_char=''):
        event_x, event_y = event_xy
        if self.x1 <= event_x <= self.x2:
            if self.y1 <= event_y <= self.y2:
                self.focus_on(color)
                print("Focus", str_char)
            else:
                self.focus_off()

    def click(self, event: Event):
        if self.x1 <= event.x <= self.x2:
            if self.y1 <= event.y <= self.y2:
                return True

    def display_keyboard(self, x=0, y=0):
        if not self.focus:
            return
        import platform
        if platform.system() == "Windows":
            # Original behaviour: launch the bundled portable on-screen keyboard.
            path = "./use_dll/On ScreenKeyboardPortable/On-ScreenKeyboardPortable"
            try:
                self.keyboard = subprocess.Popen([path])
            except FileNotFoundError:
                pass  # exe not present in this installation
        # On macOS / Linux the physical keyboard is always available — nothing needed.

    def move_on(self, color: str):
        if not self._canvas_ok():
            return
        if self.focus == False:
            try:
                self.canvas.itemconfig((self.rec), outline=color)
                if self.canvas.itemcget(self.tex, "text") == self.info1:
                    self.canvas.itemconfig((self.tex), text=(self.info2))
            except Exception:
                pass

    def move_off(self):
        if not self._canvas_ok():
            return
        if self.focus == False:
            try:
                self.canvas.itemconfig((self.rec), outline=(self.d_fill))
                if self.canvas.itemcget(self.tex, "text") == self.info2:
                    self.canvas.itemconfig((self.tex), text=(self.info1))
            except Exception:
                pass

    def Move(self, event: Event, color: str='white'):
        if self.x1 <= event.x <= self.x2:
            if self.y1 <= event.y <= self.y2:
                self.move_on(color)
            else:
                self.move_off()

    def click(self, event: Event):
        if self.x1 <= event.x <= self.x2:
            if self.y1 <= event.y <= self.y2:
                return True

    def input(self, char: str, length: int=20):
        print("char", char)
        if self.focus == True:
            value = ""
            try:
                print(char)
                value = ord(char)
                print("value", value)
            except:
                return
            else:
                if value == 8:
                    self.value = self.value[:-1]
                else:
                    if value == "":
                        self.value = ""
                    else:
                        if len(self.value) < length:
                            if not char.isspace():
                                self.value += char
                        elif self.mode == True:
                            self.info = "*" * len(self.value)
                        else:
                            self.info = self.value
                        self.canvas.itemconfig((self.tex), text=(self.info + "|"))

    def set_function(self, func=None, **kwargs):
        self.function_var = func
        self.function_args = kwargs

    def function(self):
        if self.function_var is not None:
            self.function_var(pwd=(self.function_args["pwd"]), phone_num=(self.function_args["user_entry"]), canvas=(self.function_args["canvas"]), list_player=(self.function_args["list_player"]),
              list_button=(self.function_args["list_button"]))

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/ui_design/entry_canvas.pyc
