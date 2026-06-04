# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui_game_main.py

import datetime, locale, os, shelve, sys, threading, time, tkinter, traceback
from multiprocessing import Process, Pipe
from tkinter import ttk, BOTH, YES, Canvas, Image, Tk, VERTICAL, Y, RIGHT, LEFT, messagebox
from functools import partial
from PIL import ImageTk, Image, ImageGrab
from loguru import logger
import gui.app_gui
from audio_play import audio
from database.db_operation import DBOperation
from encryption import yanqian
from game_play.game_running import GameRunning
from gui import gui_debugging, gui_setting
from gui.gui_countdown import GuiCountDown
from gui.gui_game import GuiGame
from gui.gui_game_level_select import GameLevelSelect
from gui.gui_game_ranking_canvas import GameRankingCanvas
from gui.language import language
from model.setting import Setting
from model_in.game_record_rt import GameRecordRT
from net.net_socket import NetSocket
from tourist_record.tourist_record_main import TouristRecord
from ui_design.button_canvas import Button_Canvas
from util.gm_introduce_video_new import TkVideoPlayNew
from util.idle_video_play import IdleVideoPlay
from util.image_process import ImageProcess
from util.input_listener import InputListener
from net import net_socket
from multiprocessing.connection import Connection

def process_run():
    game_idle = None
    my_log = logger.add("./log/led_play_runtime.log", retention="1 days", rotation="100 MB", level="INFO")
    game_idle = GameRunning()
    game_idle.star_running()


class GuiMain:

    def message_controller(self, conn: Connection):
        self.program_running = True
        while self.program_running:
            rcvdata = conn.recv()
            print(rcvdata)

    def dict_all_game_copy(self, dict_all_game):
        dict_game_name_new = dict()
        for key, value_list in dict_all_game.items():
            value_list_new = []
            for value in value_list:
                value_list_new.append(value.split(".")[0])

            dict_game_name_new[key] = value_list_new

        return dict_game_name_new

    def finish_game(self):
        self.reset_after_game_time_out()
        return

    def game_start(self, player_num_cur=0, tourist_name="", list_player_cur=None, root=None):
        """
        Called by GuiCountDown.next() (flag=0) after the countdown finishes.
        Resolves the selected game from the UI state, then launches GuiGame in a thread.
        """
        logger.info("game_start player_num={} tourist={}", player_num_cur, tourist_name)
        try:
            if root:
                root.destroy()
        except Exception:
            pass

        # Resolve selected game type + name from the UI buttons
        game_type = self.last_game_type.value if self.last_game_type is not None else ""
        game_name = self.last_game_name.value if self.last_game_name is not None else ""

        # Build the full file path — dict_all_game stores raw filenames (with extension)
        current_directory = os.getcwd()
        game_type_dir = os.path.join(current_directory, "source", game_type)
        list_game_path = []
        for fname in self.dict_all_game.get(game_type, []):
            if fname.split(".")[0] == game_name or fname == game_name:
                list_game_path.append(os.path.join(game_type_dir, fname))
                break

        if not list_game_path:
            logger.warning("game_start: no game found for type='{}' name='{}'", game_type, game_name)
            self.finish_game()
            return

        player_list = list_player_cur if list_player_cur else ([tourist_name] if tourist_name else [])
        life_value = self.life_value
        barcode = self.barcode_function
        game_time = self.game_time

        logger.info("game_start: path={} players={}", list_game_path, len(player_list))

        def _run():
            try:
                self.gui_game = GuiGame(self, life_value, list_game_path, barcode, game_time, player_list)
            except Exception:
                logger.error("game_start: {}", traceback.format_exc())
            finally:
                self.finish_game()
                self.game_record_rt.running_to_obj = self

        # Schedule on the main Tkinter thread so GuiUI can safely create Toplevel windows.
        # The game loop inside GuiGame calls root.update() itself, so the main thread
        # stays responsive while the game runs.
        self.root.after(0, _run)
        logger.info("game_start scheduled on main thread")

    def is_game_num_exist(self, game_type_idx, game_index):
        dict_all_game = self.dict_all_game
        list_game_type = list(dict_all_game.keys())
        game_type_length = len(list_game_type)
        if game_type_idx > game_type_length - 1 or game_type_idx < 0:
            self.game_record_rt.game_state = Setting.GAME_NUMBER_ERROR
            return False
        list_game = list(self.dict_all_game.values())[game_type_idx]
        if game_index < 0 or game_index > len(list_game):
            self.game_record_rt.game_state = Setting.GAME_NUMBER_ERROR
            return False
        return True

    def game_start_remote(self, player_num_cur=0, game_type_idx=0, game_idx=1,
                          game_time=None, tourist_name="", root=None):
        """
        Called by GuiCountDown.next() (flag=1) — used for network-triggered game start.
        game_type_idx is 0-based; game_idx is 1-based (first game = 1).
        """
        logger.info("game_start_remote type_idx={} game_idx={}", game_type_idx, game_idx)
        try:
            if root:
                root.destroy()
        except Exception:
            pass

        if not self.is_game_num_exist(game_type_idx, game_idx):
            logger.warning("game_start_remote: game index out of range")
            self.finish_game()
            self.game_record_rt.running_to_obj = self
            return

        list_types = list(self.dict_all_game.keys())
        game_type = list_types[game_type_idx]
        list_names = list(self.dict_all_game.values())[game_type_idx]
        # game_idx is 1-based
        game_name = list_names[game_idx - 1]

        current_directory = os.getcwd()
        game_path = os.path.join(current_directory, "source", game_type, game_name)
        list_game_path = [game_path]

        life_value = self.life_value
        barcode = self.barcode_function
        if game_time is None:
            game_time = self.game_time

        logger.info("game_start_remote: path={}", list_game_path)

        def _run():
            try:
                self.gui_game = GuiGame(self, life_value, list_game_path, barcode, game_time, [])
            except Exception:
                logger.error("game_start_remote: {}", traceback.format_exc())
            finally:
                self.finish_game()
                self.game_record_rt.running_to_obj = self

        self.root.after(0, _run)
        logger.info("game_start_remote scheduled on main thread")

    def game_start_thread(self, player_num_cur=0, game_type_idx=1, game_idx=1, game_time=10, play_name=None, game_level=1):
        logger.info("game_start_thread start")
        self.game_level = game_level
        self.start_button.focus_on("#66ffff")
        self.root.update()
        self.close_cur_activity()
        countdown = GuiCountDown(self, None, player_num_cur, tourist_name=play_name, game_type_idx=game_type_idx, game_idx=game_idx, game_time=game_time,
          flag=1)
        if not countdown.is_not_interrupt:
            self.finish_game()
            self.game_record_rt.running_to_obj = self
            logger.info("game_start_thread end")

    def finish_game_in_main_ui(self):
        self.game_record_rt.game_time_left = 0
        self.root.after(0, self.root_after_count_down)

    def finish_game_in_main_ui2(self):
        self.game_record_rt.reset(0, 0, 0, 0, running_to_obj=self)
        self.list_player.clear()

    def main_canvas_keyboardTest(self, event, list_item, list_entry_item):
        print("main_canvas keycode:{0},char:{1},keysym:{2}".format(event.keycode, event.char, event.keysym))
        if event.keysym == "F2":
            self.gui_setting_opened = self.gui_setting_opened or True
            logger.info("keyboard click F2")
            self.close_cur_activity()
            gui.app_gui.AppUI(self, self.setting, self.debug, self.language_var)
            logger.info("keyboard click F2 function end")
        else:
            if event.keysym == "F3":
                self.finish_game_in_main_ui()
            else:
                if event.keysym == "F4":
                    logger.info("game exit by f4")
                    self.customized_function()
        for item in list_entry_item:
            if item.focus:
                str_char = "{0}".format(event.char)
                print("str_char1", str_char)
                event = [event.x, event.y]
                item.input(str_char)

    def main_cavas_focus(self, event, list_canvas_button, list_canvas_entry):
        print("event position", event.x, event.y)
        canvas = event.widget
        canvas.focus_set()
        for button in list_canvas_button:
            if button.x1 <= event.x <= button.x2:
                if button.y1 <= event.y <= button.y2:
                    if button.btn_type == "game_type":
                        if self.last_game_type is not None:
                            if self.last_game_type != button:
                                self.last_game_type.focus_off()
                                self.last_game_type = button
                                button.focus_on("#66ffff")
                                list_game_name = self.dict_all_game[button.value]
                                logger.info("game type button {} click!", button.value)
                                self.game_name_canvas_draw_list_item(self.game_name_canvas, list_game_name)
                                self.refresh_ui_data()
                    elif button.btn_type == "game_start":
                        if not button.focus:
                            logger.info("game start button click!")
                            button.focus_on("#66ffff")
                            self.root.update()
                            if yanqian.yanqian():
                                self.close_cur_activity()
                                self.page2 = GameLevelSelect(self, self.game_level)
                                logger.info("out of gui GameLevelSelect")
                            else:
                                button.focus_off()
                                messagebox.showerror(language.AUTHOR, language.UN_AUTHOR)
                    else:
                        continue
                    if button.btn_type == "input":
                        str_char = "{0}".format(event.char)
                        print("str_char1", str_char)
                        event = [event.x, event.y]
                        button.focus_on(event, str_char=str_char)

        for item in list_canvas_entry:
            if item is not None:
                str_char = "{0}".format(event.char)
                event_xy = [
                 event.x, event.y]
                if item.b_editable:
                    item.Focus(event_xy, str_char=str_char)

        for item in list_canvas_entry:
            if item is not None:
                item.display_keyboard()

        self.last_click_time = time.time()

    def game_canvas_focus(self, event, list_canvas_button):
        canvas = event.widget
        event.x = canvas.canvasx(event.x)
        event.y = canvas.canvasy(event.y)
        for button in list_canvas_button:
            if button.x1 <= event.x <= button.x2:
                if button.y1 <= event.y <= button.y2:
                    if button.btn_type == "game_name" and self.last_game_name is not None and self.last_game_name != button:
                        self.last_game_name.focus_off()
                        self.last_game_name = button
                        button.focus_on("#66ffff")

    def program_init(self):
        self.language_var = tkinter.IntVar()
        self.language_var.set(0)
        f = shelve.open("./setting/language_parameter")
        int_lang = f.get("language_var")
        if int_lang is None:
            if locale.getdefaultlocale()[0] == "zh_CN":
                self.language_var.set(0)
                f["language_var"] = 0
            else:
                self.language_var.set(1)
                f["language_var"] = 1
        else:
            self.language_var.set(int_lang)
        f.close()
        language(self.language_var.get())
        self.audio = audio.Audio()
        self.audio.init()
        self.debug = gui_debugging.Debugging()
        self.setting = gui_setting.Setting()
        self.db = None
        try:
            self.db = DBOperation(self.setting.ip_address.get())
        except:
            logger.error(traceback.format_exc())

        self.dict_all_game = dict()
        current_directory = os.getcwd()
        game_path = os.path.join(current_directory, "source")
        self.traverse_folder(game_path)

    def traverse_folder(self, folder_path):
        try:
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isdir(file_path):
                    self.dict_all_game[file_name] = []
                    for file_name in os.listdir(file_path):
                        game_file_path = os.path.join(file_path, file_name)
                        if os.path.isfile(game_file_path):
                            parent = os.path.basename(file_path)
                            list_name = self.dict_all_game[parent]
                            file_name_tmp = file_name
                            if file_name_tmp not in list_name:
                                list_name.append(file_name_tmp)
                            print(game_file_path)

        except:
            messagebox.showerror(language.ERROR, language.GAME_DIRECTOR + language.PROBLEM)

    def game_name_canvas_draw_list_item(self, canvas, list_item, canvas_width=None):
        if canvas:
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=(self.image_file_game_list), tag="background")
            canvas.create_image(0, 0, anchor="nw", image=(self.image_file_game_list_rect), tag="background2")
            if canvas_width is not None:
                game_width = canvas_width * 14 / 20
            else:
                game_width = canvas.winfo_width() * 14 / 20
            y2 = 40
            if len(list_item) > 0:
                game_boder = 15
                start_y1 = 15
                game_height = 40
                text_color = "gray"
                list_game_name_button = []
                x1 = game_width * 8 / 40
                for i in range(len(list_item)):
                    y1 = i * (game_height + game_boder) + game_height
                    x2 = x1 + game_width
                    y2 = y1 + game_height
                    bt_game_type = Button_Canvas(canvas, x1, y1, x2, y2, (list_item[i].split(".")[0]), 15,
                      d_outline=text_color, d_fill=text_color, btn_type="game_name", no_out_line=False,
                      no_frame_img=True)
                    list_game_name_button.append(bt_game_type)

                list_game_name_button[0].focus_on("#66ffff", voice=False)
                self.last_game_name = list_game_name_button[0]
                self.last_game_name_item = list_game_name_button
            max_scroll_region_height = y2 + 20
            canvas.config(scrollregion=(0, 0, canvas.winfo_width(), max_scroll_region_height))
            canvas.bind("<Button-1>", lambda event: self.game_canvas_focus(event, list_game_name_button))
            canvas.yview_moveto(0)

    def create_game_type_wgt(self, list_game_type):
        list_game_type_img_bgm_path = [
         "./photo/game_type/game_type1.jpeg", "./photo/game_type/game_type3.jpeg",
         "./photo/game_type/game_type2.jpeg", "./photo/game_type/game_type4.jpeg"]
        scnWidth, scnHeight = self.root.maxsize()
        main_canvas = self.main_canvas
        x1 = 0.04722222222222222 * scnWidth
        y1 = 0.09 * scnHeight
        type_width = 0.2222222222222222 * scnWidth
        game_type_width_mid = x1 + type_width / 2
        game_type_height = scnHeight - 2 * y1
        num = 8
        one = game_type_height / num
        type_boder = one / 3
        type_height = 2 * one - type_boder
        game_type_height_mid_list = [one + y1, 3 * one + y1, 5 * one + y1, 7 * one + y1]
        for i in range(len(list_game_type)):
            y1 = game_type_height_mid_list[i] - type_height / 2
            y2 = game_type_height_mid_list[i] + type_height / 2
            x1 = game_type_width_mid - type_width / 2
            x2 = game_type_width_mid + type_width / 2
            bt_game_type = Button_Canvas(main_canvas, x1, y1, x2, y2, (list_game_type[i]), 25,
              d_outline="#1e90ff", d_fill="#3399ff", btn_type="game_type", image=None,
              image_path=(list_game_type_img_bgm_path[i]),
              zone_out=1.2,
              zone_in=0.9333333333333332,
              anchor="sw")
            self.list_canvas_button.append(bt_game_type)

        self.list_canvas_button[0].focus_on("#66ffff", voice=False)
        self.last_game_type = self.list_canvas_button[0]

    def update_game_type_size(self, list_game_type):
        scnWidth, scnHeight = self.root.maxsize()
        type_boder = 12
        type_width = 16 * scnWidth / 144
        game_type_number_in_one_screen = 4
        type_height = 0.20555555555555555 * scnHeight
        image_title = Image.open("./photo/new/game_type_rect.png")
        image_title = image_title.resize((round(type_width), round(type_height)), Image.LANCZOS)
        for i in range(len(list_game_type)):
            self.list_game_type_bg.append(ImageTk.PhotoImage(image_title))
            x1 = 0.022916666666666665 * scnWidth
            y1 = i * type_height + i * type_boder + 0.12222222222222222 * scnHeight
            x2 = x1 + type_width
            y2 = y1 + type_height
            bt_game_type = Button_Canvas((self.main_canvas), x1, y1, x2, y2, (list_game_type[i]), 25,
              d_outline="#1e90ff", d_fill="#3399ff", btn_type="game_type", image=(self.list_game_type_bg[i]))

    def ui_init_game_level_title(self, main_frame, start_coors):
        x_start = start_coors[0]
        y_start = start_coors[1]
        scn_width, scn_height = self.root.maxsize()
        can_tit_width = 0.0818452380952381 * scn_width
        can_tit_height = 0.040740740740740744 * scn_height
        canvas = Canvas(main_frame, bg="black", width=can_tit_width, height=can_tit_height, borderwidth=0, highlightthickness=0)
        canvas.place(x=x_start, y=y_start, anchor="center")
        region = (
         int(x_start - can_tit_width / 2), int(y_start - can_tit_height / 2),
         int(x_start + can_tit_width / 2), int(y_start + can_tit_height / 2))
        try:
            self.img_grab = ImageTk.PhotoImage(ImageGrab.grab(region))
            canvas.create_image(0, 0, anchor="nw", image=(self.img_grab))
        except Exception:
            pass
        path_img_introduce = "./photo/new/game_introduce_title_bg.png"
        self.bt_game_level_title = Button_Canvas(canvas, 0, 0, can_tit_width, can_tit_height, (language.GAME_LEVEL), no_frame_img=True,
          image_path=path_img_introduce,
          fontsize=(int(0.009375 * scn_width)),
          d_fill="white")

    def ui_init_game_introduce_title(self, main_frame, start_coors):
        x_start = start_coors[0]
        y_start = start_coors[1]
        scn_width, scn_height = self.root.maxsize()
        can_tit_width = 0.09672619047619048 * scn_width
        can_tit_height = 0.046296296296296294 * scn_height
        canvas = Canvas(main_frame, bg="black", width=can_tit_width, height=can_tit_height, borderwidth=0, highlightthickness=0)
        canvas.place(x=x_start, y=y_start, anchor="center")
        region = (
         int(x_start - can_tit_width / 2), int(y_start - can_tit_height / 2),
         int(x_start + can_tit_width / 2), int(y_start + can_tit_height / 2))
        try:
            self.img_grab_introduce = ImageTk.PhotoImage(ImageGrab.grab(region))
            canvas.create_image(0, 0, anchor="nw", image=(self.img_grab_introduce))
        except Exception:
            pass
        path_img_introduce = "./photo/new/game_introduce_title_bg.png"
        self.bt_game_introduce_title = Button_Canvas(canvas, 0, 0, can_tit_width, can_tit_height, (language.GAME_INTRODUCE), no_frame_img=True,
          image_path=path_img_introduce,
          fontsize=(int(0.009375 * scn_width)),
          d_fill="white")

    def ui_init_game_list_old(self, main_frame, scnWidth, scnHeight, image_background_path, start_coors, width, height):
        img_process = self.img_process
        path_img_bgm_game_list = "./photo/new/game_list.png"
        x_start = start_coors[0]
        game_list_y1 = start_coors[1]
        game_list_width = width
        game_list_height = height
        canvas = Canvas(main_frame, bg="#66ffff", width=game_list_width, height=(game_list_height - 5), borderwidth=0)
        canvas.place(x=x_start, y=game_list_y1, anchor="ne")
        self.game_name_canvas = canvas
        vbar = tkinter.Scrollbar(main_frame, orient=VERTICAL, borderwidth=0, bg="#66ffff")
        vbar.place(x=x_start, y=game_list_y1, anchor="nw", height=game_list_height, width=13)
        vbar.config(command=(self.custom_yview2))
        canvas.config(yscrollcommand=(vbar.set))
        canvas["highlightthickness"] = 0
        vbar["highlightthickness"] = 0
        region = (
         x_start - game_list_width, game_list_y1, x_start, game_list_y1 + game_list_height)
        self.image_file_game_list = img_process.crop_img(image_background_path, scnWidth, scnHeight, region)
        self.image_file_game_list_rect = img_process.generate(path_img_bgm_game_list, round(game_list_width), round(game_list_height))
        scnWidth, scnHeight = self.root.maxsize()
        x_start_title = 0.8645833333333334 * scnWidth
        y_start_title = 0.09814814814814815 * scnHeight
        x2 = x_start_title + width / 2
        y2 = y_start_title + width / 4
        canvas.create_text((width / 2), (height / 2), text=(language.GAME_LEVEL), font=(
         "STKaiti", int(0.009375 * scnWidth)),
          fill="yellow")

    def ui_init_game_list(self, main_frame, scnWidth, scnHeight, image_background_path, start_coors, width, height):
        img_process = self.img_process
        path_img_bgm_game_list = "./photo/new/game_list.png"
        x_start = start_coors[0]
        game_list_y1 = start_coors[1]
        game_list_width = width
        game_list_height = height
        canvas = Canvas(main_frame, bg="#66ffff", width=game_list_width, height=(game_list_height - 5), borderwidth=0)
        canvas.place(x=x_start, y=game_list_y1, anchor="ne")
        self.game_name_canvas = canvas
        vbar = tkinter.Scrollbar(main_frame, orient=VERTICAL, borderwidth=0, bg="#66ffff")
        vbar.place(x=x_start, y=game_list_y1, anchor="nw", height=game_list_height, width=13)
        vbar.config(command=(self.custom_yview2))
        self.scrollbar = vbar
        canvas.config(yscrollcommand=(vbar.set))
        canvas["highlightthickness"] = 0
        vbar["highlightthickness"] = 0
        region = (
         x_start - game_list_width, game_list_y1, x_start, game_list_y1 + game_list_height)
        self.image_file_game_list = img_process.crop_img(image_background_path, scnWidth, scnHeight, region)
        self.image_file_game_list_rect = img_process.generate(path_img_bgm_game_list, round(game_list_width), round(game_list_height))
        scnWidth, scnHeight = self.root.maxsize()
        canvas.create_text((width / 2), (height / 2), text=(language.GAME_LEVEL), font=(
         "STKaiti", int(0.009375 * scnWidth)),
          fill="yellow")
        canvas.config(scrollregion=(0, 0, canvas.winfo_width(), 2016))

    def ui_init_game_type(self, game_list_width):
        self.list_game_type_bg = []
        list_game_type = []
        for key in self.dict_all_game.keys():
            list_game_type.append(key)

        self.create_game_type_wgt(list_game_type)
        list_game_type1 = self.dict_all_game[list_game_type[0]]
        self.last_game_name_item = None
        self.game_name_canvas_draw_list_item(self.game_name_canvas, list_game_type1, game_list_width)

    def ui_init_game_introduce(self, scnWidth, scnHeight):
        img_process = self.img_process
        main_canvas = self.main_canvas
        path_img_introduce = "./photo/new/game_introduce.png"
        path_img_game_intro_video = "./photo/new/video.png"
        text_color = "yellow"
        list_color = "white"
        game_type_video = None
        text_introduce = None
        if self.last_game_type.value == self.setting.game_type_name.get():
            text_introduce = self.setting.text_introduce1.get()
            game_type_video = self.setting.game_type_video.get()
        else:
            if self.last_game_type.value == self.setting.game_type_name2.get():
                text_introduce = self.setting.text_introduce2.get()
                game_type_video = self.setting.game_type_video2.get()
            else:
                if self.last_game_type.value == self.setting.game_type_name3.get():
                    text_introduce = self.setting.text_introduce3.get()
                    game_type_video = self.setting.game_type_video3.get()
                else:
                    text_introduce = self.setting.text_introduce4.get()
                    game_type_video = self.setting.game_type_video4.get()
        x1 = 0.3125 * scnWidth
        y1 = 0.64 * scnHeight
        x2 = x1 + 0.43333333333333335 * scnWidth
        y2 = y1 + 0.5 * scnHeight * 5.1 / 10
        text_rect_width = x2 - x1
        text_rect_height = y2 - y1
        self.image_file_game_intro = img_process.generate(path_img_introduce, round(text_rect_width), round(text_rect_height))
        bt_game_introduce = Button_Canvas(main_canvas, x1, y1, x2, y2,
          text_introduce, 15,
          d_outline=text_color, d_fill=text_color, rect_vir_bord=0, image=(self.image_file_game_intro),
          no_frame_img=True)
        self.game_introduce = bt_game_introduce
        x1 = 0.3125 * scnWidth
        y1 = 0.45 * scnHeight * 5 / 20
        x2 = x1 + 0.43333333333333335 * scnWidth
        y2 = y1 + 0.675 * scnHeight * 7 / 10
        text_rect_width = x2 - x1
        text_rect_height = y2 - y1
        self.image_file_game_demo = img_process.generate(path_img_game_intro_video, round(text_rect_width), round(text_rect_height))
        video_label = tkinter.Label(main_canvas, image=(self.image_file_game_demo), borderwidth=0, border=0)
        video_label.place(x=((x1 + x2) / 2), y=((y1 + y2) / 2), anchor="center", width=text_rect_width,
          height=text_rect_height)
        self.game_type_video_path = game_type_video
        self.video_label = video_label
        image_background_path1 = "./photo/new/introduce_rect.png"
        self.img_gm_video_bg = img_process.generate(image_background_path1, text_rect_width + 22, text_rect_height + 35)
        main_canvas.create_image(((x1 + x2) / 2), ((y1 + y2) / 2.025), image=(self.img_gm_video_bg))

    def ui_init_game_start(self, scnWidth, scnHeight):
        img_process = self.img_process
        main_canvas = self.main_canvas
        list_canvas_button = self.list_canvas_button
        text_color = "yellow"
        path_img_bgm_game_start = "./photo/new/result_ranking_bg_frame1.png"
        x1 = 0.8020833333333334 * scnWidth
        y1 = scnHeight * 8 / 10
        x2 = 0.9305555555555556 * scnWidth
        y2 = y1 + scnHeight * 0.9 / 10
        text_rect_width = x2 - x1
        text_rect_height = y2 - y1
        bt_game_introduce = Button_Canvas(main_canvas, x1, y1, x2, y2, (language.NEXT), fontsize=(int(0.020833333333333332 * scnWidth)),
          d_fill="#3399ff",
          image_path=path_img_bgm_game_start,
          rect_vir_bord=0,
          btn_type="game_start",
          zone_out=1.05,
          zone_in=0.95)
        list_canvas_button.append(bt_game_introduce)
        self.start_button = bt_game_introduce

    def __init__(self):
        logger.info("game main ui")
        self.last_game_score = 0
        self.last_player_ranking = 0
        image_background_path = "./photo/game_main.png"
        self.game_record_rt = GameRecordRT()
        self.game_time = 0
        self.gui_setting_opened = False
        list_canvas_button = []
        list_canvas_entry = []
        self.list_canvas_entry = list_canvas_entry
        self.list_canvas_button = list_canvas_button
        self.list_player = []
        self.list_button = []
        self.player_num = 0
        self.entry_user_name = ""
        self.life_value = 0
        self.game_time = 0
        self.last_click_time = time.time()
        self.page2 = None
        self.page3 = None
        self.game_state = "normal"
        self.game_record_rt.running_to_obj = self
        self.cur_game = None
        self.gui_game = None
        root = Tk()
        root.attributes("-fullscreen", Setting.FULL_SCREEN)
        self.root = root
        main_frame = ttk.Frame()
        main_frame.pack(fill=BOTH, expand=YES)
        self.program_init()
        self.game_level = self.setting.game_leval.get()
        self.img_process = ImageProcess()
        img_process = self.img_process
        scnWidth = root.winfo_screenwidth()
        scnHeight = root.winfo_screenheight()
        print(scnWidth, scnHeight)
        self.game_name_canvas = None
        canvas = Canvas(main_frame, width=scnWidth, height=scnHeight, borderwidth=0)
        canvas.place(x=(scnWidth / 2), y=(scnHeight / 2), anchor="center")
        canvas["highlightthickness"] = 0
        main_canvas = canvas
        self.main_canvas = main_canvas
        main_canvas.bind("<Button-1>", lambda event: self.main_cavas_focus(event, list_canvas_button, list_canvas_entry))
        main_canvas.bind("<KeyPress>", lambda event: self.main_canvas_keyboardTest(event, list_canvas_button, list_canvas_entry))
        self.image_file_title = img_process.generate(image_background_path, scnWidth, scnHeight)
        canvas.create_image((scnWidth / 2), (scnHeight / 2), image=(self.image_file_title), tag="main_background")
        start_coors = (
         scnWidth - scnWidth / 3 / 12, 0.095 * scnHeight)
        game_list_width = scnWidth / 3 * 3.1 / 5
        game_list_height = scnHeight * 9 / 10 * 7.7 / 10
        self.text_time = canvas.create_text((scnWidth * 3.4 / 4), (1 * scnHeight / 25), text=(language.COUNT_DOWN), font=(
         "STKaiti", int(0.008333333333333333 * scnWidth), "bold"),
          fill="white")
        self.text_time_value = canvas.create_text((3.6 * scnWidth / 4), (scnHeight / 25), text="0", font=(
         "STKaiti", int(0.011458333333333333 * scnWidth), "bold"),
          fill="white")
        root.after(0, self.root_after_count_down)
        self.ui_init_game_list(main_frame, scnWidth, scnHeight, image_background_path, start_coors, game_list_width, game_list_height)
        self.ui_init_game_type(game_list_width)
        self.ui_init_game_introduce(scnWidth, scnHeight)
        self.ui_init_game_start(scnWidth, scnHeight)
        root.geometry("%dx%d+%d+%d" % (int(scnWidth), int(scnHeight), 0, 0))
        root.protocol("WM_DELETE_WINDOW", self.customized_function)
        try:
            root.iconbitmap("./photo/ledplay.ico")
        except Exception:
            pass
        root.title(language.GAME_MAIN)
        root.update()
        self.barcode_function = self.setting.barcode_function.get()
        self.player_num = self.setting.player_num.get()
        self.life_value = self.setting.life_value.get()
        self.game_time = self.setting.game_time.get()
        self.game_level = self.setting.game_leval.get()
        draw_game_level_title = threading.Thread(target=(self.ui_init_game_level_title), args=(main_frame,
         [
          start_coors[0] - game_list_width / 2, start_coors[1]]))
        draw_game_level_title.start()
        draw_game_level_title = threading.Thread(target=(self.ui_init_game_introduce_title), args=(main_frame,
         [
          0.5333333333333333 * scnWidth,
          0.09090909090909091 * scnHeight]))
        draw_game_level_title.start()
        idle_video = IdleVideoPlay(self, (self.setting.idle_video.get()), wait_time=(self.setting.idle_video_time_span.get() * 60))
        self.idle_video = idle_video
        idle_video.start()
        stop_running = partial(idle_video.reset)
        input_listener = InputListener(partial=stop_running)
        self.input_listener = input_listener
        self.gm_introduce_video = TkVideoPlayNew((self.game_type_video_path), (self.video_label), video_size=(
         self.video_label.winfo_width(), self.video_label.winfo_height()))
        self.gm_introduce_video.start()
        self.game_idle = None
        if Setting.USE_SERIAL_HD:
            self.game_idle = Process(target=process_run)
            self.game_idle.start()
        ip = self.setting.local_ip_address.get()
        port = self.setting.local_ip_port.get()
        self.socket_net = None
        if ip != "":
            if port != "":
                self.socket_net = NetSocket((ip, int(port)))
                threading.Thread(target=(self.socket_net.socket_running), args=(self,)).start()
        root.mainloop()

    def game_stop(self):
        if self.game_record_rt:
            self.game_record_rt.reset(0, 0, 0, 0, running_to_obj=self)
        if self.gui_game:
            self.gui_game.game_result()
        self.list_player.clear()

    def root_after_count_down(self, time_i=None):
        if not self.start_button.focus:
            if time_i is None:
                time = self.game_record_rt.game_time_left
            else:
                time = time_i
            if time > 0 and self.game_record_rt.game_time_left > 0:
                time_format = "{:0>2}:{:0>2}".format(int(time / 60), int(time % 60))
                self.main_canvas.itemconfig((self.text_time), state="normal")
                self.main_canvas.itemconfig((self.text_time_value), text=time_format)
                self.root.after(1000, self.root_after_count_down, time - 1)
        elif self.game_record_rt.game_time_start > 0 and time == 0:
            self.main_canvas.itemconfig((self.text_time), state="hidden")
            self.main_canvas.itemconfig((self.text_time_value), text="")
            if not self.start_button.focus:
                self.game_stop()
            self.root.after(1000, self.root_after_count_down)
        else:
            self.main_canvas.itemconfig((self.text_time), state="hidden")
            self.main_canvas.itemconfig((self.text_time_value), text="")
            self.game_record_rt.game_time_left = 0
            self.root.after(1000, self.root_after_count_down)

    def open_video_introduce(self):
        logger.info("call open_video_introduce")
        if not self.gm_introduce_video:
            self.gm_introduce_video = TkVideoPlayNew((self.game_type_video_path), (self.video_label), video_size=(
             self.video_label.winfo_width(), self.video_label.winfo_height()))
            self.gm_introduce_video.start()

    def close_video_introduce(self):
        logger.info("call close_video_introduce")
        if self.gm_introduce_video:
            self.gm_introduce_video.close_video(self.root)
            self.gm_introduce_video = None

    def close_cur_activity(self):
        if self.game_idle:
            self.game_idle.terminate()
            self.game_idle.join()
            self.game_idle.close()
            self.game_idle = None
        if self.gm_introduce_video:
            self.gm_introduce_video.close_video(self.root)
            self.gm_introduce_video = None
        if self.idle_video:
            self.idle_video.stop_running()
            self.idle_video = None

    def open_all_activity(self):
        self.open_video_introduce()
        self.open_idle_activity()

    def open_idle_activity(self):
        logger.info("call IdleVideoPlay")
        idle_video = IdleVideoPlay(self, (self.setting.idle_video.get()), wait_time=(self.setting.idle_video_time_span.get() * 60))
        self.idle_video = idle_video
        reset = partial(idle_video.reset)
        self.input_listener.partial = reset
        idle_video.start()
        logger.info("call idle game")
        if Setting.USE_SERIAL_HD:
            self.game_idle = Process(target=process_run)
            self.game_idle.start()

    def custom_yview(self, *args, **kwargs):
        canvas = self.player_canvas
        (canvas.yview)(*args, **kwargs)
        start_coors = self.tmp_coors
        x = canvas.canvasx(0)
        y = canvas.canvasy(0)
        canvas.coords("background", x, y)
        canvas.coords("background2", x, y)
        x, y = canvas.winfo_width() / 2, canvas.winfo_height() / 14
        x = canvas.canvasx(x)
        y = canvas.canvasy(y)
        canvas.coords("play_list_title_text", x, y)

    def custom_yview2(self, *args, **kwargs):
        canvas = self.game_name_canvas
        (canvas.yview)(*args, **kwargs)
        x = canvas.canvasx(0)
        y = canvas.canvasy(0)
        canvas.coords("background", x, y)
        canvas.coords("background2", x, y)

    def get_level_value(self, str_level=language.LEVAL_NORMAL):
        if str_level == language.LEVAL_SIMPLE:
            return 1
        if str_level == language.LEVAL_NORMAL:
            return 2
        return 3

    def update_self_value_after_edit(self):
        return

    def reset_after_game_time_out(self):
        logger.info("refresh_after_game")
        self.open_video_introduce()
        # Always zero the timer — game may end early (pattern completed) before
        # the clock reaches zero, in which case game_time_left stays positive and
        # root_after_count_down would keep counting down indefinitely.
        self.game_record_rt.game_time_left = 0
        if self.game_record_rt.get_game_time_pass() >= self.game_time:
            self.game_record_rt.reset(0, 0, 0, 0, running_to_obj=self)
            self.list_player.clear()
            self.open_idle_activity()
        self.root.after(0, self.root_after_count_down)
        self.start_button.focus_off()
        self.game_record_rt.running_to_flag = 0
        self.game_record_rt.running_to_obj = self

    def refresh_ui_data(self):
        logger.info("refresh main ui data")
        game_leval = self.setting.game_leval.get()
        self.barcode_function = self.setting.barcode_function.get()
        self.player_num = self.setting.player_num.get()
        self.life_value = self.setting.life_value.get()
        self.game_time = self.setting.game_time.get()
        self.game_level = self.setting.game_leval.get()
        level = language.LEVAL_SIMPLE
        if game_leval == 2:
            level = language.LEVAL_NORMAL
        else:
            if game_leval == 3:
                level = language.LEVAL_HARDER
            elif self.last_game_type.value == self.setting.game_type_name.get():
                text_introduce = self.setting.text_introduce1.get()
                game_type_video = self.setting.game_type_video.get()
            else:
                if self.last_game_type.value == self.setting.game_type_name2.get():
                    text_introduce = self.setting.text_introduce2.get()
                    game_type_video = self.setting.game_type_video2.get()
                else:
                    if self.last_game_type.value == self.setting.game_type_name3.get():
                        text_introduce = self.setting.text_introduce3.get()
                        game_type_video = self.setting.game_type_video3.get()
                    else:
                        text_introduce = self.setting.text_introduce4.get()
                        game_type_video = self.setting.game_type_video4.get()
            self.game_introduce.value_change(text_introduce)
            self.game_type_video_path = game_type_video
            if self.gm_introduce_video:
                self.gm_introduce_video.close_video(self.root)
            self.video_label.config(image=(self.image_file_game_demo))
            self.gm_introduce_video = TkVideoPlayNew(game_type_video, (self.video_label), video_size=(
             self.video_label.winfo_width(), self.video_label.winfo_height()))
            self.gm_introduce_video.start()

    def get_score(self):
        if self.gui_game:
            self.last_game_score = self.gui_game.game_scode_rule(self.setting.game_scode_divide_person.get(), self.setting.game_scode_divide_time.get(), len(self.list_player), self.game_time)

    def get_rangking(self):
        card_scan = self.setting.barcode_function.get()
        ranking_num = 50
        rangking_rst = []
        if card_scan:
            try:
                result_list = self.db.search_game_result2(ranking_num)
                for result in result_list:
                    player_scode = str(result[0])
                    player_id = result[1].split(",")[0]
                    player_info = self.db.search_custom_tb_by_id(player_id)
                    if len(player_info) > 0:
                        player_info = player_info[0]
                        if len(player_info) > 2:
                            player_phone, player_name = player_info[1], player_info[2]
                            rangking_rst.append([player_phone, player_name, player_scode])

            except:
                loguru.logger.info("db operation may be error")

        else:
            try:
                idx_name = 0
                idx_scode = 1
                text_color = "yellow"
                tourist_record = TouristRecord()
                tourist_record.connect()
                result = tourist_record.search(limit=ranking_num)
                tourist_record.close()
                for i in range(len(result)):
                    try:
                        custom_info = result[i][idx_name]
                        scode = str(result[i][idx_scode])
                        rangking_rst.append([custom_info, scode])
                    except:
                        pass

            except:
                loguru.logger.error(traceback.format_exc())

            return rangking_rst

    def customized_function(self):
        logger.info("game_main_ui close")
        for i in range(len(self.list_canvas_entry)):
            self.list_canvas_entry[i] = None

        try:
            self.gui_game.release_hw_led()
        except:
            logger.error("main gui customized_function {}", traceback.format_exc())

        if self.socket_net:
            self.socket_net.is_running = False
            self.socket_net.send(["program close"])
            self.socket_net.udp_socket.close()
        self.close_cur_activity()
        if self.db:
            self.db.close_db()
        self.root.quit()
        self.root.destroy()
# file /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui/gui_game_main.pyc
# Deparsing stopped due to parse error

