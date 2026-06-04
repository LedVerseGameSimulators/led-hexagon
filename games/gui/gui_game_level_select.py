# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui_game_level_select.py


import random, sys, time, tkinter, traceback
from threading import Thread
from tkinter import ttk
import loguru
from PIL import ImageTk, Image
from gui.gui_countdown import GuiCountDown
from gui.gui_game_ranking_canvas import GameRankingCanvas
from gui.gui_game_result import GameResult
from gui.gui_player_login import PlayerLogin
import gui.language as language
from model.setting import Setting
from tourist_record.tourist_record_main import TouristRecord
from ui_design.button_canvas import Button_Canvas
from ui_design.entry_canvas import Entry_Canvas
from util.image_process import ImageProcess
from functools import partial

class GameLevelSelect:

    def update_level_btn1(self):
        color = "#66ffff"
        self.list_btn_level_slt[0].image_path = self.list_game_level_btn_img_bgm_path[self.cur_level - 1]
        self.list_btn_level_slt[0].focus_on(color)

    def on_screen_click_level_slt(self, event, list_button):
        color = "#66ffff"
        for i, button in enumerate(list_button):
            if button.click(event):
                button.focus_on(color, voice=False)
                self.cur_level = i + 1
            else:
                button.focus_off()

        self.update_level_btn1()

    def on_screen_click_level_btn(self, event, list_button):
        color = "#66ffff"
        for button in list_button:
            if button.click(event):
                button.focus_on(color)
            else:
                button.focus_off()

    def on_screen_click_back_next_btn(self, event, list_button):
        color = "#66ffff"
        for button in list_button:
            if not button.focus:
                if button.click(event):
                    button.focus_on(color)
                else:
                    button.focus_off()

    def on_screen_keypress(self, event, list_button):
        for item in list_button:
            if item.focus:
                str_char = "{0}".format(event.char)
                item.input(str_char)

    def get_list_size_rate(self, cur_level):
        select_size_rate = 1.15
        unselect_size_rate = (3 - select_size_rate) / 2
        list_size_rate = [1, 1, 1]
        for idx, rate in enumerate(list_size_rate):
            if idx == cur_level - 1:
                list_size_rate[idx] *= select_size_rate
            else:
                list_size_rate[idx] *= unselect_size_rate

        return list_size_rate

    def create_game_level_slt(self, frame, list_game_type):
        scnWidth, scnHeight = self.root_size
        img_process = self.img_process
        self.list_canvas_button = []
        self.list_list_btn.append(self.list_canvas_button)
        canvas = tkinter.Canvas(frame, width=scnWidth, height=(scnHeight / 4), borderwidth=0, highlightthickness=0)
        canvas.pack(anchor="center")
        if self.editable:
            canvas.bind("<Button-1>", lambda event: self.on_screen_click_level_slt(event, self.list_canvas_button))
        path_img_bgm1 = "./photo/game_main.png"
        region = (0, 0, scnWidth, scnHeight / 4)
        time_bft = time.time()
        self.image_file_game_list = img_process.crop_img(path_img_bgm1, scnWidth, scnHeight, region)
        canvas.create_image(0, 0, anchor="nw", image=(self.image_file_game_list), tag="background")
        print(time.time() - time_bft)
        list_game_type_img_bgm_path = [
         "./photo/game_type/simple.jpeg", "./photo/game_type/normal.jpeg",
         "./photo/game_type/difficult.jpeg"]
        main_canvas = canvas
        type_width = scnWidth / 6
        game_type_width_mid_list = [0.25 * scnWidth, 0.5 * scnWidth, 0.75 * scnWidth]
        type_height = scnHeight / 7.2
        game_type_height_mid = 0.5 * scnHeight / 8 * 2.5
        for i in range(len(list_game_type)):
            y1 = game_type_height_mid - type_height / 2
            y2 = game_type_height_mid + type_height / 2
            x1 = game_type_width_mid_list[i] - type_width / 2
            x2 = game_type_width_mid_list[i] + type_width / 2
            bt_game_type = Button_Canvas(main_canvas, x1, y1, x2, y2, (list_game_type[i]), 25,
              d_outline="#1e90ff", d_fill="#3399ff", btn_type="game_type", image=None,
              image_path=(list_game_type_img_bgm_path[i]),
              zone_out=1.2,
              zone_in=0.9333333333333332,
              anchor="sw")
            if i == self.cur_level - 1:
                bt_game_type.focus_on("#66ffff", voice=False)
            self.list_canvas_button.append(bt_game_type)

    def create_game_level_fix(self, frame, cur_level):
        scnWidth, scnHeight = self.root_size
        img_process = self.img_process
        canvas = tkinter.Canvas(frame, width=scnWidth, height=(scnHeight / 4), borderwidth=0, highlightthickness=0)
        canvas.pack(anchor="center")
        path_img_bgm1 = "./photo/game_main.png"
        region = (0, 0, scnWidth, scnHeight / 4)
        self.img_level_fix_bg = img_process.crop_img(path_img_bgm1, scnWidth, scnHeight, region)
        canvas.create_image(0, 0, anchor="nw", image=(self.image_file_game_list), tag="background")
        self.img_level_fix = []
        img_level_fix = self.img_level_fix
        path_game_level_fix = "./photo/game_type/start.jpeg"
        type_width = scnWidth / 10
        type_height = scnWidth / 11.6
        game_type_width_mid_list = [
         0.25 * scnWidth, 0.5 * scnWidth, 0.75 * scnWidth]
        game_type_height_mid = 0.5 * scnHeight / 8 * 2.5
        for i in range(cur_level):
            img_level_fix.append(img_process.generate(path_game_level_fix, round(type_width), round(type_height)))
            canvas.create_image((game_type_width_mid_list[i]), game_type_height_mid, anchor="center", image=(img_level_fix[i]), tag="background")

    def command_level_btn_slt(self):
        self.fm_picture_2.grid_forget()
        self.fm_picture_1.grid(row=0, column=0)

    def command_level_btn_fix(self):
        self.fm_picture_1.grid_forget()
        self.fm_picture_2.grid(row=0, column=0)

    def create_level_select_button(self, frame, cur_level=1):
        list_button_name = [
         language.LEVAL, language.GAME_LIFE, language.GAME_TIME, language.AGILE]
        self.list_btn_level_slt = []
        self.list_list_btn.append(self.list_btn_level_slt)
        path_button_frame = "./photo/new/introduce_rect.PNG"
        list_game_type_img_bgm_path = self.list_game_level_btn_img_bgm_path
        scnWidth, scnHeight = self.root_size
        img_process = self.img_process
        canvas_height = scnHeight * 4 / 20
        canvas = tkinter.Canvas(frame, width=scnWidth, height=canvas_height, borderwidth=0, highlightthickness=0)
        canvas.pack(anchor="center")
        canvas.focus_set()
        canvas.bind("<Button-1>", lambda event: self.on_screen_click_level_btn(event, self.list_btn_level_slt))
        self.list_input_btn = []
        canvas.bind("<KeyPress>", lambda event: self.on_screen_keypress(event, self.list_input_btn))
        path_img_bgm1 = "./photo/game_main.png"
        region = (0, scnHeight / 4, scnWidth, scnHeight / 4 + canvas_height)
        self.img_level_slt_btn_bg = img_process.crop_img(path_img_bgm1, scnWidth, scnHeight, region)
        canvas.create_image(0, 0, anchor="nw", image=(self.img_level_slt_btn_bg), tag="background")
        type_width = scnWidth / 13.5
        game_type_width_mid_list = [0.25 * scnWidth, 0.4166666666666667 * scnWidth, 0.5833333333333334 * scnWidth, 0.75 * scnWidth]
        type_height = scnHeight / 20
        game_type_height_mid = 0.5 * scnHeight / 8 * 1.8
        btn_level_select = partial(self.command_level_btn_slt)
        btn_level_fix = partial(self.command_level_btn_fix)
        list_partial = [btn_level_select, None, None, btn_level_fix]
        for i in range(len(list_button_name)):
            y1 = game_type_height_mid - type_height / 2
            y2 = game_type_height_mid + type_height / 2
            x1 = game_type_width_mid_list[i] - type_width / 2
            x2 = game_type_width_mid_list[i] + type_width / 2
            if i == 0 or i == 3:
                bt_game_type = Button_Canvas(canvas, x1, y1, x2, y2, (list_button_name[i]), 15,
                  d_outline="#1e90ff", d_fill="#3399ff", btn_type="game_type", image=None,
                  image_path=(list_game_type_img_bgm_path[cur_level - 1]),
                  zone_out=1.05,
                  zone_in=0.95,
                  anchor="w",
                  command=(list_partial[i]))
            else:
                if i == 1:
                    bt_game_type = Entry_Canvas(canvas, ((x1 + x2) / 2), ((y1 + y2) / 2), type_width,
                      type_height,
                      text1=(str(self.life_value)), text2=(str(self.life_value)), d_fill="#3399ff",
                      fontsize=(int(0.0078125 * scnWidth)),
                      outlineboder=0,
                      flag=(str(i)),
                      text3=(list_button_name[i]),
                      image_path=path_button_frame)
                    bt_game_type.editable(self.blood_editable)
                    self.list_input_btn.append(bt_game_type)
                else:
                    bt_game_type = Entry_Canvas(canvas, ((x1 + x2) / 2), ((y1 + y2) / 2), type_width,
                      type_height,
                      text1=(str(self.game_time)), text2=(str(self.game_time)), d_fill="#3399ff",
                      fontsize=(int(0.0078125 * scnWidth)),
                      outlineboder=0,
                      flag=(str(i)),
                      text3=(list_button_name[i]),
                      image_path=path_button_frame)
                    bt_game_type.editable(self.time_editable)
                    self.list_input_btn.append(bt_game_type)
            self.list_btn_level_slt.append(bt_game_type)

    def create_ranking_image(self):
        """
        Reconstructed: builds the ranking table + BACK / NEXT buttons
        inside self.canvas_ranking.
        Called from a daemon thread started by create_ranking().
        """
        try:
            scnWidth, scnHeight = self.root_size
            canvas = self.canvas_ranking
            img_process = self.img_process
            path_img_bgm1 = "./photo/game_main.png"
            region = (0, scnHeight * 9 / 20, scnWidth, scnHeight)
            self.img_ranking_bg = img_process.crop_img(path_img_bgm1, scnWidth, scnHeight, region)
            canvas.create_image(0, 0, anchor="nw", image=self.img_ranking_bg, tag="background")

            # ── Ranking table (shows previous scores if DB available) ──────
            try:
                data = self.db.query_ranking(self.parent.last_game_type.value,
                                             self.parent.last_game_name.value) if self.db else []
            except Exception:
                data = []

            ranking_width  = scnWidth * 0.6
            ranking_height = scnHeight * 0.45
            ranking_x = scnWidth * 0.05
            ranking_y = scnHeight * 0.02
            self.ranking_canvas_widget = GameRankingCanvas(
                canvas, ranking_width, ranking_height,
                coors=[ranking_x, ranking_y],
                screen_size=(scnWidth, scnHeight),
                data=data,
                scan=self.card_scan,
            )

            # ── BACK button ───────────────────────────────────────────────
            btn_w = scnWidth / 8
            btn_h = scnHeight / 14
            back_x1 = scnWidth * 0.75
            back_y1 = scnHeight * 0.42
            back_x2 = back_x1 + btn_w
            back_y2 = back_y1 + btn_h
            path_btn = "./photo/new/introduce_rect.PNG"
            bt_back = Button_Canvas(canvas, back_x1, back_y1, back_x2, back_y2,
                                    language.BACK, 20,
                                    d_outline="#1e90ff", d_fill="#3399ff",
                                    btn_type="back",
                                    image_path=path_btn,
                                    zone_out=1.05, zone_in=0.95,
                                    command=self.back)
            self.list_btn_backornext.append(bt_back)

            # ── NEXT button ───────────────────────────────────────────────
            next_x1 = scnWidth * 0.875
            next_y1 = scnHeight * 0.42
            next_x2 = next_x1 + btn_w
            next_y2 = next_y1 + btn_h
            bt_next = Button_Canvas(canvas, next_x1, next_y1, next_x2, next_y2,
                                    language.NEXT, 20,
                                    d_outline="#1e90ff", d_fill="#3399ff",
                                    btn_type="next",
                                    image_path=path_btn,
                                    zone_out=1.05, zone_in=0.95,
                                    command=self.player_login)
            self.list_btn_backornext.append(bt_next)

        except Exception:
            import traceback
            import loguru
            loguru.logger.error("create_ranking_image error: {}", traceback.format_exc())

    def create_ranking(self, frame):
        scnWidth, scnHeight = self.root_size
        img_process = self.img_process
        self.list_btn_backornext = []
        canvas = tkinter.Canvas(frame, width=scnWidth, height=(scnHeight * 11 / 20), borderwidth=0, highlightthickness=0)
        canvas.pack(anchor="center")
        canvas.bind("<Button-1>", lambda event: self.on_screen_click_back_next_btn(event, self.list_btn_backornext))
        self.canvas_ranking = canvas
        thread = Thread(target=(self.create_ranking_image))
        thread.start()

    def ui_init_main_img_bgm(self):
        img_process = self.img_process
        canvas = self.canvas
        size = self.root_size
        path_img_bgm1 = "./photo/game_main.png"
        self.image_game_level_bg = img_process.generate(path_img_bgm1, round(size[0]), round(size[1]))
        time_bft = time.time()
        canvas.create_image((size[0] / 2), (size[1] / 2), anchor="center", image=(self.image_game_level_bg))
        print("gen img bg", time.time() - time_bft)

    def __init__(self, parent, cur_level):
        time_bft = time.time()
        root = tkinter.Toplevel()
        root.attributes("-fullscreen", Setting.FULL_SCREEN)
        size = root.maxsize()
        curWidth = size[0]
        curHeight = size[1]
        self.root_size = (curWidth, curHeight)
        self.cur_level = cur_level
        self.parent = parent
        self.db = parent.db
        self.life_value = parent.setting.life_value.get()
        self.game_time = parent.setting.game_time.get()
        self.editable = parent.setting.game_leval_editable.get()
        self.blood_editable = parent.setting.life_value_editable.get()
        self.time_editable = parent.setting.game_time_editable.get()
        self.list_list_btn = []
        self.list_game_level_btn_img_bgm_path = [
         "./photo/game_type/1star.jpg", "./photo/game_type/2star.jpg",
         "./photo/game_type/3star.jpg"]
        fm_main = tkinter.Frame(root)
        fm_main.pack()
        self.fm_main = fm_main
        self.card_scan = parent.setting.barcode_function.get()
        canvas = tkinter.Canvas(fm_main, width=curWidth, height=curHeight, borderwidth=0, highlightthickness=0)
        canvas.pack(anchor="center")
        canvas.bind("<Button-1>", lambda event: self.on_screen_click_level_btn(event))
        self.canvas = canvas
        fm_picture_2 = tkinter.Frame(canvas)
        fm_picture_2.grid(row=0, column=0)
        fm_picture_1 = tkinter.Frame(canvas)
        fm_picture_1.grid(row=0, column=0)
        fm_button = tkinter.Frame(canvas)
        fm_button.grid(row=2, column=0)
        fm_ranking = tkinter.Frame(canvas)
        fm_ranking.grid(row=3, column=0)
        self.fm_picture_1 = fm_picture_1
        self.fm_picture_2 = fm_picture_2
        self.img_process = ImageProcess()
        self.ui_init_main_img_bgm()
        list_game_leval = [
         language.LEVAL_SIMPLE, language.LEVAL_NORMAL, language.LEVAL_HARDER]
        self.create_game_level_slt(fm_picture_1, list_game_leval)
        self.create_game_level_fix(fm_picture_2, cur_level)
        self.create_level_select_button(fm_button, self.cur_level)
        self.create_ranking(fm_ranking)
        self.root = root
        root.update()
        scnWidth, scnHeight = root.maxsize()
        curWidth = scnWidth
        curHeight = scnHeight
        tmpcnf = "+%d+%d" % ((scnWidth - curWidth) / 2, (scnHeight - curHeight) / 2)
        root.geometry(tmpcnf)
        root.protocol("WM_DELETE_WINDOW", self.customized_function)
        try:
            root.iconbitmap("./photo/ledplay.ico")
        except Exception:
            pass
        root.title(language.GAME_LEVAL)
        loguru.logger.info("in gui game level select")

    def player_login(self):
        self.parent.life_value = int(self.list_input_btn[0].value)
        self.parent.game_level = self.cur_level
        if self.parent.game_record_rt.game_time_pass == 0:
            self.parent.game_time = float(self.list_input_btn[1].value)
            self.parent.page3 = PlayerLogin(self)
            self.list_btn_backornext[1].focus_off()
            loguru.logger.info("out of gui PlayerLogin")
        else:
            GuiCountDown(self.parent, self)
            loguru.logger.info("out of gui countdown")

    def back(self):
        loguru.logger.info("game level select ui back button click")
        self.root.update()
        time.sleep(0.3)
        self.list_btn_backornext[0].focus_off()
        self.list_btn_backornext.clear()
        self.customized_function()
        self.parent.reset_after_game_time_out()

    def customized_function(self):
        self.root.destroy()
# file /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui/gui_game_level_select.pyc
# Deparsing stopped due to parse error

