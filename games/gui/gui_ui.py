# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui_ui.py

import decimal, platform, time
from tkinter import Toplevel, Canvas, ttk, Frame
from PIL import ImageTk, Image
from loguru import logger
import gui.language as language

# Use a font that is always available on both macOS and Windows.
# STKaiti is a Chinese font that requires a 66 MB download on macOS.
_GAME_FONT = "PingFang SC" if platform.system() == "Darwin" else _GAME_FONT
from gui2.gui_led_table_editor import LedTable
from model.setting import Setting, Color
from util.image_process import ImageProcess

class GuiUI:

    def color_int_arr2hex_str(self, color_int_arr):
        str_hex = "#" + "{:02x}{:02x}{:02x}".format(color_int_arr[0], color_int_arr[1], color_int_arr[2])
        return str_hex

    def color_hex_str2int_arr(self, str_color):
        return (
         int(str_color[1:3], 16), int(str_color[3:5], 16), int(str_color[5:7], 16))

    def half_up(self, data):
        return int(decimal.Decimal(data).quantize((decimal.Decimal("0")), rounding=(decimal.ROUND_HALF_UP)))

    def ui_time_sleep(self, sec):
        idx = 0
        while idx < sec:
            time.sleep(0.2)
            self.root.update()
            idx += 0.2

    def closeUI(self):
        logger.info("UI close")
        self.root.update()

    def button_back(self):
        logger.info("Game UI button back click")
        self.parent.customized_function()

    def update_game_name_ui(self, game_name):
        self.canvas.itemconfig("tag_game_name", text=game_name)
        self.root.update()

    def ui_game_corporation(self, row, col, wall_light_arr_len):
        root = self.root
        self.full_screen = True
        root.attributes("-fullscreen", Setting.FULL_SCREEN)
        root.attributes("-topmost", "true")
        scnWidth, scnHeight = root.maxsize()
        canvas = Canvas(root, width=scnWidth, height=scnHeight, bg="black")
        self.canvas = canvas
        image = Image.open("./photo/game_running.jpg")
        image = image.resize((int(scnWidth), int(scnHeight)), Image.LANCZOS)
        self.bg_image_file = ImageTk.PhotoImage(image)
        canvas.create_image((int(scnWidth / 2)), (int(scnHeight / 2)), image=(self.bg_image_file))
        self.list_image = [
         None] * 5
        image = Image.open("./photo/white_heart.png")
        image = image.resize((int(scnWidth / 13), int(scnHeight / 8)), Image.LANCZOS)
        self.image_file = ImageTk.PhotoImage(image)
        for i in range(5):
            self.list_image[i] = canvas.create_image((int(scnWidth / 4) + image.width / 2 + i * int(scnWidth / 9.5)), (0.1361111111111111 * scnHeight),
              image=(self.image_file))

        canvas.pack()
        root = self.root
        canvas = self.canvas
        scnWidth, scnHeight = root.maxsize()
        divide_width = 6
        divide_height = 8
        color = "#CCFFFF"
        text_scode = canvas.create_text((0.2734375 * scnWidth), (0.6518518518518519 * scnHeight), text=(language.SCORE), font=(
         _GAME_FONT, int(0.015625 * scnWidth), "bold"),
          fill="white")
        self.text_scode_value = canvas.create_text((0.5270833333333333 * scnWidth), (0.6462962962962963 * scnHeight), text="0", font=(
         _GAME_FONT, int(0.15625 * scnWidth), "bold"),
          fill="black")
        canvas.create_text((0.43385416666666665 * scnWidth), (0.3611111111111111 * scnHeight), text=(language.COUNT_DOWN), font=(
         _GAME_FONT, int(0.010416666666666666 * scnWidth), "bold"),
          fill="black")
        self.text_time_value = canvas.create_text((0.5114583333333333 * scnWidth), (0.3611111111111111 * scnHeight), text="0", font=(
         _GAME_FONT, int(0.03125 * scnWidth), "bold"),
          fill="black")
        canvas.create_text((0.50625 * scnWidth), (0.8981481481481481 * scnHeight), text="", font=(
         _GAME_FONT, int(0.03125 * scnWidth), "bold"),
          fill="white",
          tag="tag_game_name")
        x1 = scnWidth - 0.06770833333333333 * scnWidth
        x2 = x1 + int(0.0625 * scnWidth)
        y1 = scnHeight - 0.09259259259259259 * scnHeight
        y2 = y1 + int(0.037037037037037035 * scnHeight)
        a = ttk.Style()
        a.configure("my.TButton", font=(_GAME_FONT, int(0.015625 * scnWidth), "bold"), foreground="gray")
        ttk.Button(canvas, text=(language.BACK), style="my.TButton", width=6, command=(self.button_back)).place(relx=0.9,
          rely=0.9)
        table_frame = Frame(root)
        self.led_table = LedTable(table_frame, wall_light_arr_len, row, col)
        size = self.led_table.get_canvas_table_size()
        table_frame.place(relx=(5 / scnWidth), rely=(1 - (size[1] + 100) / scnHeight))
        root.update()
        root.state("zoomed")
        curWidth = root.winfo_width()
        curHeight = root.winfo_height()
        print(curWidth, curHeight)
        scnWidth, scnHeight = root.maxsize()
        tmpcnf = "+%d+%d" % ((scnWidth - curWidth) / 2, (scnHeight - curHeight) / 2)
        root.geometry(tmpcnf)
        root.protocol("WM_DELETE_WINDOW", self.parent.customized_function)
        root.iconbitmap("./photo/ledplay.ico")

    def draw_hexagon3(self, canvas, center_x, center_y, size, fill='gray', outline='gray'):
        size = size / 2
        points = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        size = size * 2 / 3
        points2 = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        size = size * 1 / 2
        points3 = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        polygon1 = canvas.create_polygon(points, fill=fill, outline="black")
        polygon2 = canvas.create_polygon(points2, fill=fill, outline="black")
        polygon3 = canvas.create_polygon(points3, fill=fill, outline="black")
        return (
         polygon1, polygon2, polygon3)

    def ui_editor_game2(self, row, col, gun_nums):
        root = self.root
        img_pro = self.img_process
        player_nums = self.parent.player_nums
        list_player_name = self.parent.list_player_name
        list_score = self.parent.color_scode
        list_bullet = self.parent.color_bullet
        list_color = self.parent.color_array
        root.attributes("-fullscreen", Setting.FULL_SCREEN)
        root.attributes("-topmost", "true")
        scnWidth, scnHeight = root.maxsize()
        canvas = Canvas(root, width=scnWidth, height=scnHeight, bg="black", borderwidth=0, highlightthickness=0)
        canvas.pack()
        self.bg_image_file = img_pro.generate("./photo/laser/laser_running_bgm.png", scnWidth, scnHeight)
        canvas.create_image((int(scnWidth / 2)), (int(scnHeight / 2)), image=(self.bg_image_file))
        color_hig_start = scnHeight / 11
        color_hig_start2 = scnHeight / 13.4
        color = "white"
        canvas.create_text((0.640625 * scnWidth), color_hig_start, text=(language.COUNT_DOWN + language.COLON),
          font=(_GAME_FONT, int(0.008854166666666666 * scnWidth)),
          fill=color)
        self.text_time_value = canvas.create_text((0.7291666666666666 * scnWidth), color_hig_start2, text="0", tags="clock", font=(
         _GAME_FONT, int(0.03125 * scnWidth), "bold"),
          fill=color)
        self.list_image = [
         None] * 5
        self.image_file = self.img_process.generate("./photo/white_heart.png", int(scnWidth / 13), int(scnHeight / 8))
        for i in range(5):
            self.list_image[i] = canvas.create_image((int(scnWidth / 4) + self.image_file.width() / 2 + i * int(scnWidth / 9.5)), (0.2777777777777778 * scnHeight),
              image=(self.image_file))

        canvas.pack()
        self.list_hexagon = [
         None, None]
        for i in range(2):
            self.list_hexagon[i] = self.draw_hexagon3(canvas, scnWidth * 0.6 / 5 + i * 19 * scnWidth / 25, scnHeight / 2, 400)

        width_start_title = scnWidth / 10
        height_start_title = scnHeight / 2
        row_size = scnHeight / 5
        width_span_content = scnWidth * 4 / 5 / player_nums
        width_start_content = scnWidth * 0.1 + scnWidth * 0.8 / (player_nums * 2)
        canvas.create_text(width_start_title, height_start_title, text=(language.PLAYER),
          font=(_GAME_FONT, int(0.005208333333333333 * scnWidth)),
          fill=color)
        canvas.create_text(width_start_title, (height_start_title + row_size), text=(language.SCORE),
          font=(_GAME_FONT, int(0.005208333333333333 * scnWidth)),
          fill=color)
        size = 60 + (6 - player_nums) * 20
        if size < 60:
            size = 60
        for i in range(player_nums):
            canvas.create_text((width_start_content + width_span_content * i), height_start_title, text=(list_player_name[i]),
              font=(_GAME_FONT, int(size * 1 / 3 / 1920 * scnWidth)),
              fill=(self.color_int_arr2hex_str(list_color[i][0])))
            canvas.create_text((width_start_content + width_span_content * i), (height_start_title + row_size), text=(list_score[i]),
              font=(_GAME_FONT, int(size / 1920 * scnWidth)),
              fill=(self.color_int_arr2hex_str(list_color[i][0])),
              tags=("score" + str(i + 1)))

        canvas.create_text((0.2708333333333333 * scnWidth), (0.07407407407407407 * scnHeight), text="", font=(
         _GAME_FONT, int(0.015625 * scnWidth), "bold"),
          fill="white",
          tag="tag_game_name")
        self.canvas = canvas
        a = ttk.Style()
        a.configure("my.TButton", font=(_GAME_FONT, int(0.015625 * scnWidth), "bold"), foreground="gray")
        ttk.Button(canvas, text=(language.BACK), style="my.TButton", width=6, command=(self.button_back)).place(relx=0.9,
          rely=0.93)
        table_frame = Frame(root)
        self.led_table = LedTable(table_frame, gun_nums, row, col)
        size = self.led_table.get_canvas_table_size()
        table_frame.place(relx=(5 / scnWidth), rely=(1 - (size[1] + 100) / scnHeight))
        root.update()
        curWidth = root.winfo_width()
        curHeight = root.winfo_height()
        print(curWidth, curHeight)
        scnWidth, scnHeight = root.maxsize()
        tmpcnf = "+%d+%d" % ((scnWidth - curWidth) / 2, (scnHeight - curHeight) / 2)
        root.geometry(tmpcnf)
        root.protocol("WM_DELETE_WINDOW", self.parent.customized_function)
        root.iconbitmap("./photo/ledplay.ico")

    def ui_game_battle(self, row, col, wall_light_arr_len):
        root = self.root
        self.full_screen = True
        root.attributes("-fullscreen", Setting.FULL_SCREEN)
        root.attributes("-topmost", "true")
        scnWidth, scnHeight = root.maxsize()
        canvas = Canvas(root, width=scnWidth, height=scnHeight, bg="black")
        self.canvas = canvas
        canvas.bind("<Double-Button-1>", lambda event: self.screen_mouse_event(event, root))
        image = Image.open("./photo/caise.png")
        image = image.resize((int(scnWidth), int(scnHeight)), Image.LANCZOS)
        self.bg_image_file = ImageTk.PhotoImage(image)
        canvas.create_image((int(scnWidth / 2)), (int(scnHeight / 2)), image=(self.bg_image_file))
        self.left_list_image = [
         None] * 5
        self.right_list_image = [None] * 5
        red_heart = "./photo/white_heart.png"
        img_process = ImageProcess()
        self.image_red_heart = img_process.generate(red_heart, int(scnWidth / 12), int(scnHeight / 7))
        yellow_star = "./photo/game_type/start.JPEG"
        self.image_yellow_star = img_process.generate(yellow_star, int(scnWidth / 11.8), int(scnHeight / 6.8))
        width_start = 0
        height_start = int(scnHeight / 6)
        color = "#CCFFFF"
        canvas.create_text((scnWidth / 4), (scnHeight / 2.5), text="", font=(
         _GAME_FONT, int(0.078125 * scnWidth)),
          fill=color,
          tags="text_game_result_left")
        for i in range(1, 6, 1):
            self.left_list_image[i - 1] = canvas.create_image((width_start + i * (scnWidth / 10) - scnWidth / 20), height_start,
              image=(self.image_red_heart))

        width_start = int(scnWidth / 2)
        canvas.create_text((scnWidth * 3 / 4), (scnHeight / 2.5), text="", font=(
         _GAME_FONT, int(0.078125 * scnWidth)),
          fill=color,
          tags="text_game_result_right")
        for i in range(1, 6, 1):
            self.right_list_image[i - 1] = canvas.create_image((width_start + i * (scnWidth / 9.9) - scnWidth / 19.8), height_start,
              image=(self.image_yellow_star))

        canvas.pack()
        root = self.root
        canvas = self.canvas
        scnWidth, scnHeight = root.maxsize()
        divide_width = 6
        divide_height = 8
        first_positon_x = 2 * scnWidth / divide_width
        two_position_x = 4 * scnWidth / divide_width
        three_position_y = scnHeight - scnHeight / divide_height
        three_position_x = scnWidth - scnWidth / divide_width
        two_position_y = 4 * scnHeight / divide_height
        lable_start_position_width = scnWidth / 3 / 2
        lable_start_position_height = scnHeight - scnHeight / 10
        lable_width = scnWidth / 3
        position_index = 0
        value_start_position_width = lable_start_position_width
        value_start_position_height = 0.65 * scnHeight
        value_width = lable_width
        canvas.create_text((lable_start_position_width + position_index * lable_width), lable_start_position_height, text=(language.SCORE),
          font=(_GAME_FONT, int(0.026041666666666668 * scnWidth)),
          fill=color)
        self.text_scode_value_left = canvas.create_text((value_start_position_width + position_index * value_width), value_start_position_height,
          text="0", font=(
         _GAME_FONT, int(0.078125 * scnWidth)),
          fill="white")
        position_index += 1
        canvas.create_text((lable_start_position_width + position_index * lable_width), lable_start_position_height, text=(language.TIME),
          font=(_GAME_FONT, int(0.026041666666666668 * scnWidth)),
          fill=color)
        self.text_time_value = canvas.create_text((value_start_position_width + position_index * value_width), value_start_position_height,
          text="0", font=(
         _GAME_FONT, int(0.052083333333333336 * scnWidth)),
          fill="white")
        position_index += 1
        canvas.create_text((lable_start_position_width + position_index * lable_width), lable_start_position_height, text=(language.SCORE),
          font=(_GAME_FONT, int(0.026041666666666668 * scnWidth)),
          fill=color)
        self.text_scode_value_right = canvas.create_text((value_start_position_width + position_index * value_width), value_start_position_height,
          text="0", font=(
         _GAME_FONT, int(0.078125 * scnWidth)),
          fill="white")
        a = ttk.Style()
        a.configure("my.TButton", font=(_GAME_FONT, int(0.015625 * scnWidth), "bold"), foreground="gray")
        ttk.Button(canvas, text=(language.BACK), style="my.TButton", width=6, command=(self.button_back)).place(relx=0.9,
          rely=0.93)
        table_frame = Frame(root)
        self.led_table = LedTable(table_frame, wall_light_arr_len, row, col)
        size = self.led_table.get_canvas_table_size()
        table_frame.place(relx=(5 / scnWidth), rely=(1 - (size[1] + 100) / scnHeight))
        root.update()
        curWidth = root.winfo_width()
        curHeight = root.winfo_height()
        print(curWidth, curHeight)
        scnWidth, scnHeight = root.maxsize()
        tmpcnf = "+%d+%d" % ((scnWidth - curWidth) / 2, (scnHeight - curHeight) / 2)
        root.geometry(tmpcnf)
        root.protocol("WM_DELETE_WINDOW", self.parent.customized_function)
        root.iconbitmap("./photo/ledplay.ico")

    def reset_life_value_ui_DECOMPILE_ERROR(self, *args):
        pass  # decompiler parse error

    def update_life_value_ui_1(self, life_value):
        end_idx = self.half_up(5 * life_value / self.blood_total)
        if end_idx < 1:
            end_idx = 1
        for i in range(4, end_idx - 1, -1):
            if self.list_image[i] is not None:
                self.canvas.itemconfig((self.list_image[i]), state="hidden")

    def update_goal_light_color(self, color_arr):
        if not color_arr:
            return
        for j in range(len(color_arr)):
            for i in range(3):
                fomat_color = self.color_int_arr2hex_str(color_arr[j][i])
                self.canvas.itemconfig((self.list_hexagon[j][i]), fill=fomat_color)

    def update_data_ui(self, scode, life_vale, time=0):
        if scode >= 0:
            scode_format = "{:0>4}".format(scode)
        else:
            scode_format = "-{:0>3}".format(abs(scode))
        if time < 0:
            time = 0
        time_format = "{:0>2}:{:0>2}".format(int(time / 60), int(time % 60))
        self.canvas.itemconfig((self.text_scode_value), text=scode_format)
        self.canvas.itemconfig((self.text_time_value), text=time_format)
        self.update_life_value_ui_1(life_vale)
        if -2 < life_vale <= 0:
            self.reset_life_value_ui()
        self.root.update()

    def update_life_value_ui_2(self, game_record):
        game1_blood = game_record.game_blood_left
        game2_blood = game_record.game_blood_right
        if -2 < game1_blood <= 0:
            game_record.game_blood_left = game1_blood = self.blood_total
            self.reset_life_value_ui(0)
        if -2 < game2_blood <= 0:
            game_record.game_blood_right = game2_blood = self.blood_total
            self.reset_life_value_ui(1)
        end_idx = self.half_up(5 * game1_blood / self.blood_total)
        for i in range(4, end_idx - 1, -1):
            if self.left_list_image[i] is not None:
                self.canvas.itemconfig((self.left_list_image[i]), state="hidden")

        end_idx = self.half_up(5 * game2_blood / self.blood_total)
        for i in range(4, end_idx - 1, -1):
            if self.right_list_image[i] is not None:
                self.canvas.itemconfig((self.right_list_image[i]), state="hidden")

    def update_editor_game1(self, game_record):
        game1_scode = game_record.game_scode_left
        game2_scode = game_record.game_scode_right
        time_left = game_record.game_time_left
        if game1_scode >= 0:
            left_scode_format = "{:0>4}".format(game1_scode)
        else:
            left_scode_format = "-{:0>3}".format(abs(game1_scode))
        if game2_scode >= 0:
            right_scode_format = "{:0>4}".format(game2_scode)
        else:
            right_scode_format = "-{:0>3}".format(abs(game2_scode))
        if time_left < 0:
            time_left = 0
        time_format = "{:0>2}:{:0>2}".format(int(time_left / 60), int(time_left % 60))
        self.canvas.itemconfig((self.text_scode_value_left), text=left_scode_format)
        self.canvas.itemconfig((self.text_scode_value_right), text=right_scode_format)
        self.canvas.itemconfig((self.text_time_value), text=time_format)
        self.update_life_value_ui_2(game_record)
        self.root.update()

    def update_editor_game2(self, game_record):
        game2_scode = game_record.game_scode_right
        time_left = game_record.game_time_left
        list_score = game_record.game_info[0]
        life_vale = game_record.game_blood
        list_format_score = []
        for score in list_score:
            if score >= 0:
                score = "{:0>4}".format(score)
            else:
                score = "-{:0>3}".format(abs(score))
            list_format_score.append(score)

        list_format_bullet = []
        if time_left < 0:
            time_left = 0
        time_format = "{:0>2}:{:0>2}".format(int(time_left / 60), int(time_left % 60))
        self.canvas.itemconfig("clock", text=time_format)
        for i in range(len(list_score)):
            self.canvas.itemconfig(("score" + str(i + 1)), text=(list_format_score[i]))

        self.update_life_value_ui_1(life_vale)
        self.update_goal_light_color(game_record.game_info2)
        if life_vale <= 0:
            self.reset_life_value_ui()
        self.root.update()

    def update_ui(self, game_record=None, time_pass=0):
        mode = self.mode
        if self.led_table.canvas:
            self.led_table.draw_canvas(self.wall_line)
            self.root.update()
        elif game_record:
            if mode == 0:
                if game_record.game_blood <= 0:
                    game_record.game_result = 0
                self.update_data_ui(game_record.game_scode, game_record.game_blood, game_record.game_time_left)
            else:
                if mode == 1:
                    self.update_editor_game1(game_record)
                else:
                    if mode == 2:
                        if game_record.game_blood <= 0:
                            game_record.game_result = 0
                        elif time_pass > 0:
                            self.cur_time_count += time_pass
                            if self.cur_time_count > self.update_frequency:
                                self.cur_time_count = 0
                                self.update_editor_game2(game_record)
                        else:
                            self.update_editor_game2(game_record)

    def reset_result_text(self):
        self.canvas.itemconfig("text_game_result_left", text="")
        self.canvas.itemconfig("text_game_result_right", text="")
        self.reset_life_value_ui(0)
        self.reset_life_value_ui(1)

    def update_result_text(self, score1, score2):
        if score1 < score2:
            side = 1
        else:
            if score1 > score2:
                side = 0
            else:
                side = -1
        if side == 0:
            rig_color = Color.RED_FORMAT
            lft_color = Color.GREEN_FORMAT
            rig_text = language.LOSE
            lft_text = language.WIN
        else:
            if side == 1:
                rig_color = Color.GREEN_FORMAT
                lft_color = Color.RED_FORMAT
                rig_text = language.WIN
                lft_text = language.LOSE
            else:
                rig_color = Color.GREEN_FORMAT
                lft_color = Color.GREEN_FORMAT
                rig_text = language.TIE
                lft_text = language.TIE
        self.canvas.itemconfig("text_game_result_left", text=lft_text, fill=lft_color)
        self.canvas.itemconfig("text_game_result_right", text=rig_text, fill=rig_color)
        print("update_result_text")

    def __init__(self, parent, blood_total, led_row, led_col, wall_light_arr_len, wall_line, mode=0):
        self.root = Toplevel()
        self.img_process = ImageProcess()
        self.blood_total = blood_total
        self.wall_line = wall_line
        self.mode = mode
        self.parent = parent
        self.update_frequency = 0.5
        self.cur_time_count = 0
        parent.game_record_rt.running_to_flag = 1
        if mode == 0:
            self.ui_game_corporation(led_row, led_col, wall_light_arr_len)
        else:
            if mode == 1:
                self.ui_game_battle(led_row, led_col, wall_light_arr_len)
            else:
                if mode == 2:
                    self.ui_editor_game2(led_row, led_col, wall_light_arr_len)

    def ui_loop(self):
        self.root.mainloop()
# file /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui/gui_ui.pyc
# Deparsing stopped due to parse error

